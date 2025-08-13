"""
Experiment script to compare route policies on a synthetic 10-stop cold chain.

This module runs the ColdChainModel using different route policies and logs
total travel time and total remaining shelf life at deliveries. The results
are written to a CSV file for further analysis.
"""
import pandas as pd

from coldchain_sim import graph as graph_mod
from coldchain_sim.model import ColdChainModel
from coldchain_sim.config import DEFAULT_SKUS, SIM
from coldchain_sim.policies.heuristics import NearestNeighborPolicy, TwoOptPolicy, path_time
from coldchain_sim.policies.ortools_tsp import ORToolsTSPPolicy
from coldchain_sim.objectives import total_time_minutes, total_remaining_life_at_deliveries


def _pick_graph(n_customers=10, seed=7):
    """
    Prefer an asymmetric/noisy graph to better separate policies.
    Fallback to the original symmetric graph if needed.
    """
    if hasattr(graph_mod, "synthetic_asymmetric_graph"):
        return graph_mod.synthetic_asymmetric_graph(
            n_customers=n_customers, seed=seed, scale=12.0, asymmetry=0.5, jitter=0.35
        )
    # fallback
    return graph_mod.synthetic_10_stop_graph(seed=seed)


def _units_delivered(model: ColdChainModel) -> int:
    return sum(sum(s["per_sku_qty"].values()) for s in model.rem_life_log_per_stop)


def _avg_minutes_per_unit(model: ColdChainModel) -> float:
    total_weighted = total_remaining_life_at_deliveries(model)  # sum of quantity-weighted minutes
    units = _units_delivered(model)
    return (total_weighted / units) if units else 0.0


def _demands_10x4():
    # Ten stops, four SKUs
    return {
        n: {"strawberries": 20, "romaine": 15, "blueberries": 12, "spinach": 10}
        for n in range(1, 11)
    }


def _capacity_trailer():
    return {
        "strawberries": 300,
        "romaine": 220,
        "blueberries": 180,
        "spinach": 160,
    }


def run(policy):
    """
    Run a simulation with the given route policy. Returns a dict
    with route preview and simulation KPIs.
    """
    G = _pick_graph(n_customers=10, seed=7)
    demands = _demands_10x4()
    capacity = _capacity_trailer()

    # Preview the route this policy produces (independent of the model run)
    route = policy.build_route(G, depot=0, customers=sorted(demands.keys()))
    route_minutes = path_time(route, G)

    # Build & run model
    model = ColdChainModel(G, policy, demands, capacity, SIM, DEFAULT_SKUS, seed=123)
    model.run_until_done()

    # Metrics
    time_total = total_time_minutes(model)
    life_total = total_remaining_life_at_deliveries(model)  # quantity-weighted minutes
    deliveries = len(model.rem_life_log_per_stop)
    units = _units_delivered(model)
    avg_min_per_unit = _avg_minutes_per_unit(model)

    return {
        "policy": policy.__class__.__name__,
        "route_minutes": route_minutes,
        "time_total": time_total,
        "life_total": life_total,
        "deliveries": deliveries,
        "units_delivered": units,
        "avg_minutes_per_unit": avg_min_per_unit,
        "avg_hours_per_unit": (avg_min_per_unit / 60.0) if avg_min_per_unit else 0.0,
        "route": route,
    }


def main():
    rows = []
    for policy in (NearestNeighborPolicy(), TwoOptPolicy(), ORToolsTSPPolicy()):
        rows.append(run(policy))
    df = pd.DataFrame(rows)

    # Save results to CSV
    df.to_csv("results.csv", index=False)
    print(df[
        ["policy", "route_minutes", "time_total", "life_total", "deliveries",
         "units_delivered", "avg_minutes_per_unit", "avg_hours_per_unit"]
    ])


if __name__ == "__main__":
    main()
