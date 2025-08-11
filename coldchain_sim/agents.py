from mesa import Agent
import math
from .shelf_life import q10_degradation_per_min


class DistributionCenter(Agent):
    def step(self):
        pass


class Store(Agent):
    def __init__(self, uid, model, node_id, sku_demands, service_minutes):
        super().__init__(uid, model)
        self.node_id = node_id
        self.sku_demands = dict(sku_demands)
        self.service_minutes = service_minutes
        self.served = False

    def step(self):
        pass


class Vehicle(Agent):
    def __init__(self, uid, model, route, capacity_by_sku, sim_p, sku_params):
        super().__init__(uid, model)
        self.route = route[:]
        self.next_ix = 1
        self.pos = self.route[0]
        self.remaining_travel = 0
        self.inventory = dict(capacity_by_sku)
        self.setpoint = sim_p.setpoint_c
        self.trailer_temp = sim_p.setpoint_c
        self.sim_p = sim_p
        self.ambient = lambda t: 18 + 6*math.sin((t/60.0-6)/24*2*math.pi)
        self.service_timer = 0
        self.drive_min = 0
        self.service_min = 0
        self.completed = False

        self.sku_params = sku_params
        self.life_remaining_min = {k: v.L_ref_hours*60 for k, v in sku_params.items()}

    def step(self):
        if self.completed:
            return
        # cooling toward setpoint
        self.trailer_temp += self.sim_p.cool_rate_per_min * (self.setpoint - self.trailer_temp)
        if self.remaining_travel > 0:
            self.remaining_travel -= 1
            self.drive_min += 1
        else:
            if self.service_timer > 0:
                self.service_timer -= 1
                self.service_min += 1
                amb = self.ambient(self.model.time_minute)
                self.trailer_temp += self.sim_p.temp_drift_ambient * (amb - self.trailer_temp)
            else:
                if self.next_ix >= len(self.route):
                    self.completed = True
                else:
                    nxt = self.route[self.next_ix]
                    if nxt == self.pos:
                        self._service_here()
                    else:
                        t = self.model.graph[self.pos][nxt]["time"]
                        self.remaining_travel = max(int(t), 1)
                        self.pos = nxt
                        self.next_ix += 1

        # degrade shelf life
        for sku, qty in self.inventory.items():
            if qty <= 0:
                continue
            p = self.sku_params[sku]
            d = q10_degradation_per_min(p.L_ref_hours, self.trailer_temp, p.T_ref, p.Q10)
            self.life_remaining_min[sku] = max(0.0, self.life_remaining_min[sku] - d)

    def _service_here(self):
        store = self.model.store_by_node.get(self.pos)
        if store and not store.served:
            self.trailer_temp += self.sim_p.temp_spike_on_open
            for sku, need in store.sku_demands.items():
                take = min(self.inventory.get(sku, 0), need)
                self.inventory[sku] = self.inventory.get(sku, 0) - take
                store.sku_demands[sku] -= take
            store.served = True
            self.service_timer = store.service_minutes
