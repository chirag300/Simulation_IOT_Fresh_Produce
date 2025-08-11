from .base import RoutePolicy

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
    best = route[:]
    improved = True
    while improved:
        improved = False
        for i in range(1, len(best) - 2):
            for j in range(i + 1, len(best) - 1):
                new = best[:i] + best[i:j][::-1] + best[j:]
                if path_time(new, G) < path_time(best, G):
                    best = new
                    improved = True
    return best

def path_time(route, G):
    t = 0
    for a, b in zip(route, route[1:]):
        t += G[a][b]["time"]
    return t
