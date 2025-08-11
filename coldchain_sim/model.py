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

        # Log remaining life at each delivery
        self.rem_life_log = []

        self.datacollector = DataCollector(
            model_reporters={
                "minute": lambda m: m.time_minute,
                "time_so_far": total_time_minutes,
            }
        )

    def step(self):
        pre_served = {n: s.served for n, s in self.store_by_node.items()}
        self.datacollector.collect(self)
        self.schedule.step()
        post_served = {n: s.served for n, s in self.store_by_node.items()}
        for n, s in self.store_by_node.items():
            if post_served[n] and not pre_served[n]:
                life_sum = sum(self.vehicle.life_remaining_min.values())
                self.rem_life_log.append(life_sum)
        self.time_minute += 1

    def run_until_done(self, max_minutes=None):
        cap = max_minutes or self.sim_p.max_minutes
        for _ in range(cap):
            self.step()
            if self.vehicle.completed:
                break
