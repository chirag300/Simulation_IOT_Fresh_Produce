# coldchain_sim/graph.py
import math
import random
import networkx as nx


def synthetic_10_stop_graph(seed: int = 7, scale: float = 12.0) -> nx.DiGraph:
    """
    Original symmetric toy instance:
    - depot = 0 centered
    - 10 customers on random coordinates
    - complete directed graph with symmetric times (rounded Euclidean * scale)
    """
    rnd = random.Random(seed)
    G = nx.DiGraph()

    # positions in [0,1]x[0,1]
    coords = {0: (0.5, 0.5)}
    for i in range(1, 11):
        coords[i] = (rnd.random(), rnd.random())

    for u in range(0, 11):
        for v in range(0, 11):
            if u == v:
                continue
            (x1, y1), (x2, y2) = coords[u], coords[v]
            base = math.hypot(x1 - x2, y1 - y2) * scale
            t = max(1, int(round(base)))
            G.add_edge(u, v, time=t)

    return G


def synthetic_asymmetric_graph(
    n_customers: int = 10,
    seed: int = 7,
    scale: float = 12.0,
    asymmetry: float = 0.5,
    jitter: float = 0.35,
) -> nx.DiGraph:
    """
    Asymmetric/noisy instance to separate heuristics:
    time(u->v) = round( |u-v|_euclid * scale * (1+dir_bias) * (1+eps) ), >= 1
    where dir_bias ~ U[-asymmetry, asymmetry], eps ~ U[-jitter, jitter]
    """
    rnd = random.Random(seed)
    G = nx.DiGraph()

    coords = {0: (0.5, 0.5)}
    for i in range(1, n_customers + 1):
        coords[i] = (rnd.random(), rnd.random())

    for u in range(0, n_customers + 1):
        for v in range(0, n_customers + 1):
            if u == v:
                continue
            (x1, y1), (x2, y2) = coords[u], coords[v]
            base = math.hypot(x1 - x2, y1 - y2) * scale
            dir_bias = asymmetry * (rnd.random() - 0.5) * 2.0
            eps = jitter * (rnd.random() - 0.5) * 2.0
            t = max(1, int(round(base * (1.0 + dir_bias) * (1.0 + eps))))
            G.add_edge(u, v, time=t)

    return G
