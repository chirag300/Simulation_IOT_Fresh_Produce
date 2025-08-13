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

G = synthetic_10_stop_graph(seed=7)
policy = ORToolsTSPPolicy()
m = ColdChainModel(G, policy, demands, capacity, SIM, DEFAULT_SKUS)
m.run_until_done()
df = m.datacollector.get_model_vars_dataframe()
print(df.tail())
print(
    "Remaining-life (sum over stops & SKUs):",
    sum(sum(snap.values()) for snap in m.rem_life_log_per_stop),
)
