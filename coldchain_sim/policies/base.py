from abc import ABC, abstractmethod

class RoutePolicy(ABC):
    @abstractmethod
    def build_route(self, graph, depot, customers):
        """return list like [0, i1, i2, ..., 0]"""

    def valid_route(self, route, depot, customers):
        return route[0] == depot and route[-1] == depot and \
               set(route[1:-1]) == set(customers) and len(route) == len(customers) + 2
