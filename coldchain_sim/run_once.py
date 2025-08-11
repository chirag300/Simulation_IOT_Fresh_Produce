from coldchain_sim.graph import synthetic_10_stop_graph
from coldchain_sim.policies.heuristics import NearestNeighborPolicy
from coldchain_sim.model import ColdChainModel
from coldchain_sim.config import DEFAULT_SKUS, SIM

demands = {n: {"strawberries": 20, "romaine": 15} for n in range(1, 11)}
capacity = {"strawberries": 300, "romaine": 220}

G = synthetic_10_stop_graph(seed=7)
policy = NearestNeighborPolicy()
m = ColdChainModel(G, policy, demands, capacity, SIM, DEFAULT_SKUS)
m.run_until_done()
df = m.datacollector.get_model_vars_dataframe()
print(df.tail())
print("Remaining-life sum:", sum(m.rem_life_log))
