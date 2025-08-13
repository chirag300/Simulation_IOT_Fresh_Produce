"""
Route policy using OR-Tools to solve a traveling salesman problem.

This policy constructs a route that starts and ends at the depot and visits
each customer exactly once, minimizing total travel time.  If OR-Tools is
not installed or fails to find a solution within the time limit, it falls
back to the nearest-neighbor heuristic.
"""
from .base import RoutePolicy


class ORToolsTSPPolicy(RoutePolicy):
    """
    Route policy that solves a TSP on the given graph using OR-Tools.
    """

    def build_route(self, G, depot, customers):
        """
        Build a route using OR-Tools.  Returns a list of node IDs starting
        at depot, visiting each customer once, and returning to the depot.
        Falls back to NearestNeighborPolicy if OR-Tools is unavailable or no
        solution is found within the time limit.
        """
        try:
            # OR-Tools is an optional dependency
            from ortools.constraint_solver import pywrapcp, routing_enums_pb2
        except Exception:
            from .heuristics import NearestNeighborPolicy
            return NearestNeighborPolicy().build_route(G, depot, customers)

        # Build list of nodes (depot + customers)
        nodes = [depot] + list(customers)
        n = len(nodes)
        # Build distance matrix for OR-Tools
        # The order in 'nodes' defines indices in the matrix.
        M = [[0] * n for _ in range(n)]
        for i, a in enumerate(nodes):
            for j, b in enumerate(nodes):
                if i != j:
                    # ensure integer cost
                    M[i][j] = int(G[a][b]["time"])

        # Create the routing index manager and model for a single vehicle
        manager = pywrapcp.RoutingIndexManager(n, 1, 0)  # start depot index = 0
        routing = pywrapcp.RoutingModel(manager)

        # Define cost callback
        def distance_callback(i, j):
            return M[manager.IndexToNode(i)][manager.IndexToNode(j)]

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Set search parameters
        search_params = pywrapcp.DefaultRoutingSearchParameters()
        search_params.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_params.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        # Limit search time to a few seconds
        search_params.time_limit.FromSeconds(2)

        # Solve the problem
        solution = routing.SolveWithParameters(search_params)
        if solution is None:
            # Fall back to nearest neighbor if no solution found
            from .heuristics import NearestNeighborPolicy
            return NearestNeighborPolicy().build_route(G, depot, customers)

        # Extract the route
        index = routing.Start(0)
        order = []
        while not routing.IsEnd(index):
            order.append(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))
        # Add final node (should be depot)
        order.append(manager.IndexToNode(index))
        # Map back to actual node IDs
        route = [nodes[i] for i in order]
        # Ensure route ends at depot
        if route[-1] != depot:
            route.append(depot)
        return route