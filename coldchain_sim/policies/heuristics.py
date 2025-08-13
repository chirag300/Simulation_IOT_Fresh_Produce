from .base import RoutePolicy

def path_time(route, G):
    return sum(G[a][b]["time"] for a, b in zip(route, route[1:]))

class NearestNeighborPolicy(RoutePolicy):
    def build_route(self, G, depot, customers):
        unvisited = set(customers)
        route = [depot]
        cur = depot
        while unvisited:
            nxt = min(unvisited, key=lambda j: G[cur][j]["time"])
            route.append(nxt)
            unvisited.remove(nxt)
            cur = nxt
        route.append(depot)
        return route

def two_opt(route, G):
    """Simple 2-opt improvement over a feasible route (keeps depot endpoints)."""
    best = route[:]
    improved = True
    while improved:
        improved = False
        # don't break start/end (index 0 and -1 are depots)
        for i in range(1, len(best) - 2):
            for j in range(i + 1, len(best) - 1):
                new = best[:i] + best[i:j][::-1] + best[j:]
                if path_time(new, G) < path_time(best, G):
                    best = new
                    improved = True
    return best

class TwoOptPolicy(RoutePolicy):
    """NN seed + 2-opt local search."""
    def build_route(self, G, depot, customers):
        nn = NearestNeighborPolicy().build_route(G, depot, customers)
        return two_opt(nn, G)
