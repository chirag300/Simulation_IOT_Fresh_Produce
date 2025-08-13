"""
Matplotlib live visualization of a single run:
- left: network with depot (blue), stores (gray->green when served), and vehicle (red dot)
- top-right: trailer temperature over time
- bottom-right: avg remaining minutes per unit delivered so far
"""

import argparse
import math
import random
import matplotlib.pyplot as plt
import matplotlib.animation as anim
import networkx as nx

from coldchain_sim import graph as graph_mod
from coldchain_sim.model import ColdChainModel
from coldchain_sim.config import DEFAULT_SKUS, SIM
from coldchain_sim.policies.heuristics import NearestNeighborPolicy, TwoOptPolicy
from coldchain_sim.policies.ortools_tsp import ORToolsTSPPolicy

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
    total = sum(s["total_weighted_minutes"] for s in model.rem_life_log_per_stop)
    u = units_delivered(model)
    return (total / u) if u else 0.0

def layout_in_unit_square(G, seed=7):
    rnd = random.Random(seed)
    pos = {}
    if 0 in G.nodes:
        pos[0] = (0.5, 0.5)
    for n in G.nodes:
        if n == 0: continue
        pos[n] = (rnd.random(), rnd.random())
    return pos

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--asymmetric", action="store_true")
    ap.add_argument("--policy", choices=["nn", "twoopt", "ort"], default="ort")
    args = ap.parse_args()

    policy = {"nn": NearestNeighborPolicy(), "twoopt": TwoOptPolicy(), "ort": ORToolsTSPPolicy()}[args.policy]

    G = pick_graph(10, args.seed, use_asym=args.asymmetric)
    dem = demands_10x4()
    cap = capacity_trailer()

    model = ColdChainModel(G, policy, dem, cap, SIM, DEFAULT_SKUS, seed=args.seed)

    # static layout for plotting
    pos = layout_in_unit_square(G, seed=args.seed)

    # figure
    fig = plt.figure(figsize=(10, 6))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.2, 1.0], height_ratios=[1, 1])

    ax_net = fig.add_subplot(gs[:, 0])
    ax_temp = fig.add_subplot(gs[0, 1])
    ax_avg = fig.add_subplot(gs[1, 1])

    # draw base network
    dep_color = "#2b6cb0"   # blue
    store_color = "#a0aec0" # gray
    served_color = "#2f855a" # green
    veh_color = "#c53030"   # red

    nx.draw_networkx_edges(G, pos, ax=ax_net, alpha=0.2)
    nx.draw_networkx_nodes(G, pos, nodelist=[0], node_color=dep_color, node_size=200, ax=ax_net)
    store_nodes = [n for n in G.nodes if n != 0]
    store_scat = ax_net.scatter([pos[n][0] for n in store_nodes],
                                [pos[n][1] for n in store_nodes],
                                s=120, c=store_color, zorder=3)

    veh_scat = ax_net.scatter([pos[0][0]], [pos[0][1]], s=160, c=veh_color, zorder=4)
    ax_net.set_title("Cold Chain: Vehicle & Deliveries")
    ax_net.set_xticks([]); ax_net.set_yticks([])

    # temp trace
    temp_x, temp_y = [], []
    (temp_line,) = ax_temp.plot([], [], lw=1.5)
    ax_temp.set_title("Trailer Temperature (°C)")
    ax_temp.set_xlabel("minute"); ax_temp.set_ylabel("°C")

    # avg remaining life per unit trace
    avg_x, avg_y = [], []
    (avg_line,) = ax_avg.plot([], [], lw=1.5)
    ax_avg.set_title("Average Remaining Life per Unit (minutes)")
    ax_avg.set_xlabel("minute"); ax_avg.set_ylabel("min")

    # animation step
    def update(_frame):
        # one model minute
        if not model.vehicle.completed:
            model.step()

        # update store colors
        colors = []
        for n in store_nodes:
            served = model.store_by_node[n].served
            colors.append(served_color if served else store_color)
        store_scat.set_color(colors)

        # vehicle position (snap to current node)
        vpos = pos[model.vehicle.pos]
        veh_scat.set_offsets([[vpos[0], vpos[1]]])

        # temp line
        temp_x.append(model.time_minute)
        temp_y.append(model.vehicle.trailer_temp)
        temp_line.set_data(temp_x, temp_y)
        ax_temp.relim(); ax_temp.autoscale_view()

        # avg life per unit delivered
        avg_x.append(model.time_minute)
        avg_y.append(avg_minutes_per_unit(model))
        avg_line.set_data(avg_x, avg_y)
        ax_avg.relim(); ax_avg.autoscale_view()

        return (store_scat, veh_scat, temp_line, avg_line)

    ani = anim.FuncAnimation(fig, update, interval=50, blit=False)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
