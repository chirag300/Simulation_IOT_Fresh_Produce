"""
Route policy using OR-Tools to solve a traveling salesman problem.

If OR-Tools is unavailable or no solution is found within the time limit,
falls back to NearestNeighborPolicy.
"""
from .base import RoutePolicy
from .heuristics import NearestNeighborPolicy, path_time

class ORToolsTSPPolicy(RoutePolicy):
    def build_route(self, G, depot, customers):
        try:
            from ortools.constraint_solver import pywrapcp, routing_enums_pb2
        except Exception:
            print("[ORToolsTSP] OR-Tools not available; falling back to NearestNeighbor.")
            return NearestNeighborPolicy().build_route(G, depot, customers)

        nodes = [depot] + list(customers)
        n = len(nodes)

        # Distance matrix (integers)
        M = [[0] * n for _ in range(n)]
        for i, a in enumerate(nodes):
            for j, b in enumerate(nodes):
                if i != j:
                    M[i][j] = int(G[a][b]["time"])

        manager = pywrapcp.RoutingIndexManager(n, 1, 0)
        routing = pywrapcp.RoutingModel(manager)

        def distance_callback(i, j):
            return M[manager.IndexToNode(i)][manager.IndexToNode(j)]

        transit_idx = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_idx)

        search = pywrapcp.DefaultRoutingSearchParameters()
        search.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        search.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        search.time_limit.FromSeconds(5)

        solution = routing.SolveWithParameters(search)
        if solution is None:
            print("[ORToolsTSP] No solution found; falling back to NearestNeighbor.")
            return NearestNeighborPolicy().build_route(G, depot, customers)

        # Extract route in index space
        idx = routing.Start(0)
        order = []
        while not routing.IsEnd(idx):
            order.append(manager.IndexToNode(idx))
            idx = solution.Value(routing.NextVar(idx))
        order.append(manager.IndexToNode(idx))

        # Map back to node ids
        route = [nodes[i] for i in order]
        if route[-1] != depot:
            route.append(depot)

        print(f"[ORToolsTSP] used OR-Tools. route_minutes={path_time(route, G)} route={route}")
        return route

    def valid_route(self, route, depot, customers):
        return (route[0] == depot and route[-1] == depot and
                set(route[1:-1]) == set(customers) and len(route) == len(customers) + 2)
