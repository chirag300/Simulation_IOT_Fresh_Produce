from mesa import Agent
import math
from .shelf_life import q10_degradation_per_min
from .temps import DiurnalWithDoor

class DistributionCenter(Agent):
    def step(self): pass

class Store(Agent):
    def __init__(self, uid, model, node_id, sku_demands, service_minutes):
        super().__init__(uid, model)
        self.node_id = node_id
        self.sku_demands = dict(sku_demands)
        self.service_minutes = service_minutes
        self.served = False
    def step(self): pass

class Vehicle(Agent):
    def __init__(self, uid, model, route, capacity_by_sku, sim_p, sku_params):
        super().__init__(uid, model)
        self.route = route[:]                 # [0, i1, ..., 0]
        self.next_ix = 1
        self.pos = self.route[0]
        self.remaining_travel = 0
        self.inventory = dict(capacity_by_sku)
        self.sim_p = sim_p
        # Temperature model: synthetic IoT sensor capturing diurnal ambient,
        # cooling, drift when doors are open, and random noise.  This object
        # encapsulates all temperature dynamics and holds the current trailer
        # temperature in its `temp` attribute.
        self.temp_model = DiurnalWithDoor(
            setpoint=sim_p.setpoint_c,
            cool_rate=sim_p.cool_rate_per_min,
            drift=sim_p.temp_drift_ambient,
            open_spike=sim_p.temp_spike_on_open,
        )

        self.service_timer = 0
        self.drive_min = 0
        self.service_min = 0
        self.completed = False

        self.sku_params = sku_params
        self.life_remaining_min = {k: v.L_ref_hours*60 for k, v in sku_params.items()}

    def step(self):
        if self.completed: return

        # Determine ambient temperature for this minute
        amb = self.temp_model.ambient(self.model.time_minute)

        if self.remaining_travel > 0:
            self.remaining_travel -= 1
            self.drive_min += 1
            # Doors are closed while driving
            self.temp_model.tick_closed()
        else:
            if self.service_timer > 0:
                self.service_timer -= 1
                self.service_min += 1
                # Doors are open during service: trailer drifts toward ambient
                self.temp_model.tick_open(amb)
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
                        # Begin driving to next node: doors closed
                        self.temp_model.tick_closed()

        # shelf-life decay for carried items
        for sku, qty in self.inventory.items():
            if qty <= 0: continue
            p = self.sku_params[sku]
            # Use current trailer temperature from the temp model for Q10 decay
            d = q10_degradation_per_min(p.L_ref_hours, self.temp_model.temp, p.T_ref, p.Q10)
            self.life_remaining_min[sku] = max(0.0, self.life_remaining_min[sku] - d)
        # Update trailer_temp attribute for backward compatibility (may be used in KPIs)
        self.trailer_temp = self.temp_model.temp

    def _service_here(self):
        store = self.model.store_by_node.get(self.pos)
        if store and not store.served:
            # Apply instantaneous spike when doors open for service
            self.temp_model.bump_on_open()
            for sku, need in store.sku_demands.items():
                take = min(self.inventory.get(sku, 0), need)
                self.inventory[sku] = self.inventory.get(sku, 0) - take
                store.sku_demands[sku] -= take
            store.served = True
            self.service_timer = store.service_minutes
