from fastapi import APIRouter

from app import queries
from app.db.graph_database import GraphDatabase


def create_routes(graph_database: GraphDatabase) -> APIRouter:
    router = APIRouter()

    @router.post('/vertex/count')
    def count_vertex_by_label():
        g = graph_database.get_read_traversal()
        return queries.count_vertex_by_label(g)

    @router.post('/edges/count')
    def count_edge_by_label():
        g = graph_database.get_read_traversal()
        return queries.count_edge_by_label(g)

    return router
