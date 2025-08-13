"""
Experiment script to compare route policies on a synthetic 10-stop cold chain.

This module runs the ColdChainModel using different route policies and logs
total travel time and total remaining shelf life at deliveries.  The results
are written to a CSV file for further analysis.
"""
import pandas as pd

from coldchain_sim.graph import synthetic_10_stop_graph
from coldchain_sim.model import ColdChainModel
from coldchain_sim.config import DEFAULT_SKUS, SIM
from coldchain_sim.policies.heuristics import NearestNeighborPolicy
from coldchain_sim.policies.ortools_tsp import ORToolsTSPPolicy


def run(policy):
    """
    Run a simulation with the given route policy.  Returns a dict
    containing the policy name, total time (drive + service), and total
    remaining shelf life across all SKUs at all stops.
    """
    G = synthetic_10_stop_graph(seed=7)
    # Build demands for 10 stops and four SKUs
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
    model = ColdChainModel(G, policy, demands, capacity, SIM, DEFAULT_SKUS, seed=123)
    model.run_until_done()
    df = model.datacollector.get_model_vars_dataframe()
    time_total = df["time_so_far"].iloc[-1]
    # Sum of remaining life across all SKUs and all stops
    life_total = 0.0
    for snap in model.rem_life_log_per_stop:
        life_total += sum(snap.values())
    return {
        "policy": policy.__class__.__name__,
        "time_total": time_total,
        "life_total": life_total,
    }


def main():
    rows = []
    for policy in [NearestNeighborPolicy(), ORToolsTSPPolicy()]:
        rows.append(run(policy))
    df = pd.DataFrame(rows)
    # Save results to CSV
    df.to_csv("results.csv", index=False)
    print(df)


if __name__ == "__main__":
    main()