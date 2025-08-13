"""
Monte Carlo experiment:
- Runs multiple random seeds across several route policies
- Aggregates KPIs (time, remaining freshness, averages)
- Reports the best policy per seed and overall
- Writes results to mc_results.csv
"""

import argparse
import statistics as stats
import pandas as pd

from coldchain_sim import graph as graph_mod
from coldchain_sim.model import ColdChainModel
from coldchain_sim.config import DEFAULT_SKUS, SIM
from coldchain_sim.policies.heuristics import NearestNeighborPolicy, TwoOptPolicy, path_time
from coldchain_sim.policies.ortools_tsp import ORToolsTSPPolicy
from coldchain_sim.objectives import (
    total_time_minutes,
    total_remaining_life_at_deliveries as life_total_weighted,
    weighted_score,  # time - beta*life
)

# ---------- helpers ----------

def pick_graph(n_customers, seed, use_asym=True):
    if use_asym and hasattr(graph_mod, "synthetic_asymmetric_graph"):
        return graph_mod.synthetic_asymmetric_graph(
            n_customers=n_customers, seed=seed, scale=12.0, asymmetry=0.5, jitter=0.35
        )
    return graph_mod.synthetic_10_stop_graph(seed=seed, scale=12.0)

def demands_10x4():
    return {
        n: {"strawberries": 20, "romaine": 15, "blueberries": 12, "spinach": 10}
        for n in range(1, 11)
    }

def capacity_trailer():
    return {"strawberries": 300, "romaine": 220, "blueberries": 180, "spinach": 160}

def units_delivered(model):
    return sum(sum(s["per_sku_qty"].values()) for s in model.rem_life_log_per_stop)

def avg_minutes_per_unit(model):
    total = life_total_weighted(model)
    u = units_delivered(model)
    return (total / u) if u else 0.0

def route_minutes(G, policy, customers):
    route = policy.build_route(G, 0, customers)
    return path_time(route, G), route

# ---------- single run ----------

def run_once(seed, policy, use_asym=True):
    G = pick_graph(n_customers=10, seed=seed, use_asym=use_asym)
    dem = demands_10x4()
    cap = capacity_trailer()

    # preview route (so it’s comparable if the model logic changes)
    r_minutes, route = route_minutes(G, policy, sorted(dem.keys()))

    m = ColdChainModel(G, policy, dem, cap, SIM, DEFAULT_SKUS, seed=seed)
    m.run_until_done()

    row = {
        "seed": seed,
        "policy": policy.__class__.__name__,
        "route_minutes": r_minutes,
        "time_total": total_time_minutes(m),
        "life_total": life_total_weighted(m),  # quantity-weighted minutes
        "units_delivered": units_delivered(m),
        "avg_minutes_per_unit": avg_minutes_per_unit(m),
        "score_alpha": 1.0,
        "score_beta": 1e-3,
        "weighted_score": weighted_score(m, alpha=1.0, beta=1e-3),  # smaller is better
        "deliveries": len(m.rem_life_log_per_stop),
        "route": route,
    }
    return row

# ---------- CLI ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20, help="Number of random seeds")
    ap.add_argument("--start-seed", type=int, default=1, help="First seed value")
    ap.add_argument("--asymmetric", action="store_true", help="Use asymmetric graph")
    ap.add_argument("--outfile", default="mc_results.csv")
    args = ap.parse_args()

    policies = [NearestNeighborPolicy(), TwoOptPolicy(), ORToolsTSPPolicy()]
    rows = []
    for s in range(args.start_seed, args.start_seed + args.seeds):
        for p in policies:
            rows.append(run_once(s, p, use_asym=args.asymmetric))

    df = pd.DataFrame(rows)
    df.to_csv(args.outfile, index=False)

    # Per-seed winners by weighted score (lower is better)
    winners = (
        df.loc[df.groupby("seed")["weighted_score"].idxmin()]
        .sort_values(["weighted_score"])
        .reset_index(drop=True)
    )

    # Overall summary
    by_policy = (
        df.groupby("policy")
          .agg(
              runs=("policy", "count"),
              route_minutes_mean=("route_minutes", "mean"),
              time_total_mean=("time_total", "mean"),
              life_total_mean=("life_total", "mean"),
              avg_min_per_unit_mean=("avg_minutes_per_unit", "mean"),
              weighted_score_mean=("weighted_score", "mean"),
              weighted_score_std=("weighted_score", "std"),
          )
          .reset_index()
    )

    print("\n=== Monte Carlo Summary by Policy ===")
    print(by_policy.to_string(index=False, float_format=lambda x: f"{x:,.3f}"))

    print("\n=== Seed Winners (by weighted_score) ===")
    print(winners[["seed", "policy", "weighted_score", "route_minutes", "time_total"]]
          .to_string(index=False, float_format=lambda x: f"{x:,.3f}"))

    print(f"\nSaved detailed results to {args.outfile}")

if __name__ == "__main__":
    main()
