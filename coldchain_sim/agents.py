from mesa import Agent
from .shelf_life import q10_degradation_per_min
from .temps import DiurnalWithDoor


class DistributionCenter(Agent):
    def step(self) -> None:
        pass


class Store(Agent):
    def __init__(self, uid, model, node_id, sku_demands, service_minutes):
        super().__init__(uid, model)
        self.node_id = node_id
        self.sku_demands = dict(sku_demands)
        self.service_minutes = service_minutes
        self.served = False

    def step(self) -> None:
        pass


class Vehicle(Agent):
    def __init__(self, uid, model, route, capacity_by_sku, sim_p, sku_params):
        super().__init__(uid, model)
        # Route state: route = [0, i1, ..., 0]
        self.route = route[:]
        self.pos = self.route[0]
        self.next_ix = 1                 # next waypoint index in route
        self.remaining_travel = 0        # minutes left to arrive
        self.travel_target = None        # node we are currently heading to

        # Ops bookkeeping
        self.drive_min = 0
        self.service_min = 0
        self.service_timer = 0
        self.completed = False

        # Inventory & shelf-life
        self.inventory = dict(capacity_by_sku)
        self.sku_params = sku_params
        self.life_remaining_min = {k: v.L_ref_hours * 60 for k, v in sku_params.items()}

        # Temperature model (synthetic IoT sensor dynamics)
        self.sim_p = sim_p
        self.temp_model = DiurnalWithDoor(
            setpoint=sim_p.setpoint_c,
            cool_rate=sim_p.cool_rate_per_min,
            drift=sim_p.temp_drift_ambient,
            open_spike=sim_p.temp_spike_on_open,
        )
        self.trailer_temp = self.temp_model.temp  # exposed for KPIs

        # Delivery event (set when a delivery happens this minute)
        self.just_delivered_event = None

    def step(self) -> None:
        if self.completed:
            return

        # reset event for this minute
        self.just_delivered_event = None

        # Ambient temperature this minute
        amb = self.temp_model.ambient(self.model.time_minute)

        if self.remaining_travel > 0:
            # Driving toward travel_target
            self.remaining_travel -= 1
            self.drive_min += 1
            self.temp_model.tick_closed()

            # Arrive exactly when remaining_travel hits zero
            if self.remaining_travel == 0 and self.travel_target is not None:
                self.pos = self.travel_target
                self.travel_target = None
                # Do NOT auto-serve in the same minute; serving happens when we next hit the idle branch

        else:
            # Not driving
            if self.service_timer > 0:
                # Currently servicing (doors open)
                self.service_timer -= 1
                self.service_min += 1
                self.temp_model.tick_open(amb)

            else:
                # Idle at a node: first, serve here if it's a store not yet served
                store_here = self.model.store_by_node.get(self.pos)
                if store_here and not store_here.served:
                    self._service_here()
                else:
                    # Otherwise, decide to move to the next waypoint or finish
                    if self.next_ix >= len(self.route):
                        self.completed = True
                    else:
                        nxt = self.route[self.next_ix]
                        if nxt == self.pos:
                            # Edge case: duplicate node in route; mark as served if applicable
                            self._service_here()
                            self.next_ix += 1
                        else:
                            # Start traveling (do not change pos yet)
                            t = self.model.graph[self.pos][nxt]["time"]
                            self.remaining_travel = max(int(t), 1)
                            self.travel_target = nxt
                            self.next_ix += 1
                            self.temp_model.tick_closed()

        # Shelf-life decay for items still on board (Q10 with current trailer temp)
        for sku, qty in self.inventory.items():
            if qty <= 0:
                continue
            p = self.sku_params[sku]
            d = q10_degradation_per_min(p.L_ref_hours, self.temp_model.temp, p.T_ref, p.Q10)
            self.life_remaining_min[sku] = max(0.0, self.life_remaining_min[sku] - d)

        # Update exposed temperature value
        self.trailer_temp = self.temp_model.temp

    def _service_here(self) -> None:
        store = self.model.store_by_node.get(self.pos)
        if store and not store.served:
            # Doors open: instantaneous spike
            self.temp_model.bump_on_open()

            delivered = {}
            for sku, need in store.sku_demands.items():
                have = self.inventory.get(sku, 0)
                take = min(have, need)
                if take > 0:
                    self.inventory[sku] = have - take
                    store.sku_demands[sku] = need - take
                    delivered[sku] = take

            store.served = True
            self.service_timer = store.service_minutes

            # Snapshot per-SKU remaining life (minutes) at the delivery moment
            life_now = self.life_remaining_min.copy()

            # Emit event so the model logs exactly once with quantities
            self.just_delivered_event = {
                "node": self.pos,
                "delivered_qty": delivered,   # dict[sku] -> units delivered
                "life_at_delivery": life_now, # dict[sku] -> minutes remaining
            }
