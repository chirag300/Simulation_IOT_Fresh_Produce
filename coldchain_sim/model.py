from mesa import Model
from mesa.time import BaseScheduler
from mesa.datacollection import DataCollector
from mesa.space import NetworkGrid
from .agents import DistributionCenter, Store, Vehicle
from .config import SIM, DEFAULT_SKUS
from .objectives import total_time_minutes


class ColdChainModel(Model):
    def __init__(self, graph, policy, demands, capacity_by_sku,
                 sim_params=SIM, sku_params=DEFAULT_SKUS, seed=123):
        super().__init__(seed=seed)
        self.graph = graph
        self.grid = NetworkGrid(graph)
        self.schedule = BaseScheduler(self)
        self.time_minute = 0
        self.sim_p = sim_params
        self.sku_params = sku_params
        self.depot = 0

        # DC
        self.dc = DistributionCenter("DC", self)
        self.grid.place_agent(self.dc, self.depot)
        self.schedule.add(self.dc)

        # Stores
        self.store_by_node = {}
        for node, dem in demands.items():
            s = Store(f"S{node}", self, node, dem, self.sim_p.service_minutes)
            self.grid.place_agent(s, node)
            self.schedule.add(s)
            self.store_by_node[node] = s

        # Route from policy (enforces depot start/end and single visit)
        customers = sorted(demands.keys())
        route = policy.build_route(graph, self.depot, customers)
        assert policy.valid_route(route, self.depot, customers), "Invalid route from policy."

        # Vehicle
        self.vehicle = Vehicle("Truck", self, route, capacity_by_sku, self.sim_p, self.sku_params)
        self.grid.place_agent(self.vehicle, self.depot)
        self.schedule.add(self.vehicle)

        # Logs
        # Sum of quantity-weighted remaining shelf life across all SKUs per delivery
        self.rem_life_log = []
        # Rich per-stop snapshot
        self.rem_life_log_per_stop = []

        # Time series (minute-level)
        self.datacollector = DataCollector(
            model_reporters={
                "minute": lambda m: m.time_minute,
                "time_so_far": total_time_minutes,
                "life_strawberries": lambda m: m.vehicle.life_remaining_min.get("strawberries", 0.0),
                "life_romaine":      lambda m: m.vehicle.life_remaining_min.get("romaine", 0.0),
                "life_blueberries":  lambda m: m.vehicle.life_remaining_min.get("blueberries", 0.0),
                "life_spinach":      lambda m: m.vehicle.life_remaining_min.get("spinach", 0.0),
            }
        )

    def step(self):
        # Collect minute-t metrics BEFORE agents act
        self.datacollector.collect(self)

        # Advance all agents; Vehicle may set just_delivered_event
        self.schedule.step()

        # Log delivery exactly once (if it happened this minute)
        ev = getattr(self.vehicle, "just_delivered_event", None)
        if ev:
            life_at_delivery = ev["life_at_delivery"]   # dict[sku] -> minutes
            delivered_qty = ev["delivered_qty"]         # dict[sku] -> units

            # Quantity-weighted remaining life (minutes × units)
            weighted = {
                sku: life_at_delivery.get(sku, 0.0) * delivered_qty.get(sku, 0.0)
                for sku in self.sku_params.keys()
            }
            total_weighted_minutes = sum(weighted.values())

            self.rem_life_log.append(total_weighted_minutes)
            self.rem_life_log_per_stop.append({
                "node": ev["node"],
                "per_sku_minutes": life_at_delivery,
                "per_sku_qty": delivered_qty,
                "per_sku_qty_weighted_minutes": weighted,
                "total_weighted_minutes": total_weighted_minutes,
            })

            # consume event
            self.vehicle.just_delivered_event = None

        self.time_minute += 1

    def run_until_done(self, max_minutes=None):
        cap = max_minutes or self.sim_p.max_minutes
        for _ in range(cap):
            self.step()
            if self.vehicle.completed:
                break
