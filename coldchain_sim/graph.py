import networkx as nx
import random


def synthetic_10_stop_graph(seed=42):
    random.seed(seed)
    G = nx.complete_graph(11, create_using=nx.DiGraph)
    # nodes 0..10
    for i, j in G.edges():
        if i == j:
            continue
        base = 6 + abs(i - j) + random.randint(0, 6)
        G[i][j]["time"] = base
    return G
