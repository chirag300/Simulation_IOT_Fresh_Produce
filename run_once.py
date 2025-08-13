# run_once.py
from coldchain_sim.graph import synthetic_10_stop_graph
from coldchain_sim.policies.ortools_tsp import ORToolsTSPPolicy
from coldchain_sim.model import ColdChainModel
from coldchain_sim.config import DEFAULT_SKUS, SIM

# Build demands for ten stops with four SKUs
demands = {
    n: {"strawberries": 20, "romaine": 15, "blueberries": 12, "spinach": 10}
    for n in range(1, 11)
}

# Trailer capacity for each SKU
capacity = {
    "strawberries": 300,
    "romaine": 220,
    "blueberries": 180,
    "spinach": 160,
}

# Graph + policy
G = synthetic_10_stop_graph(seed=7)
policy = ORToolsTSPPolicy()

# Model
m = ColdChainModel(G, policy, demands, capacity, SIM, DEFAULT_SKUS)
m.run_until_done()

# Time series (minute-level)
df = m.datacollector.get_model_vars_dataframe()
print(df.tail())

# Delivery-level logs
deliveries_logged = len(m.rem_life_log_per_stop)
life_total = sum(s["total_weighted_minutes"] for s in m.rem_life_log_per_stop)

print("Deliveries logged:", deliveries_logged)
print("Remaining-life (quantity-weighted minutes, summed over all stops & SKUs):", life_total)

# Optional: peek at the last delivery snapshot for sanity
if m.rem_life_log_per_stop:
    last = m.rem_life_log_per_stop[-1]
    print("Last delivery snapshot (node, total_weighted_minutes):", last["node"], last["total_weighted_minutes"])
