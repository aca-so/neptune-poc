from fastapi import APIRouter
from gremlin_python.process.graph_traversal import __

from app.db.graph_database import GraphDatabase


def create_routes(graph_database: GraphDatabase) -> APIRouter:
    router = APIRouter()

    @router.post('/vertex/count')
    async def count_vertex_by_label():
        g = graph_database.get_read_traversal()
        return g.V().groupCount().by(__.label()).next()

    @router.post('/edges/count')
    async def count_edge_by_label():
        g = graph_database.get_read_traversal()
        return g.E().groupCount().by(__.label()).next()

    return router
