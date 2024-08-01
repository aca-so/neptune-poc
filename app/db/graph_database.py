from abc import ABC, abstractmethod

from gremlin_python.process.graph_traversal import GraphTraversalSource


class GraphDatabase(ABC):
    @abstractmethod
    def get_traversal(self) -> GraphTraversalSource:
        pass

    @abstractmethod
    def get_read_traversal(self) -> GraphTraversalSource:
        pass

    @abstractmethod
    async def close(self):
        pass
