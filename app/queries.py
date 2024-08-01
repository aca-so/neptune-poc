import asyncio

from gremlin_python.process.graph_traversal import GraphTraversalSource, __


async def count_vertex_by_label(g: GraphTraversalSource):
    def func():
        return g.V().groupCount().by(__.label()).next()
    return await asyncio.to_thread(func)


async def count_edge_by_label(g: GraphTraversalSource):
    def func():
        return g.E().groupCount().by(__.label()).next()
    return await asyncio.to_thread(func)
