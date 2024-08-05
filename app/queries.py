from asyncio import wrap_future

from gremlin_python.process.graph_traversal import GraphTraversalSource, __, GraphTraversal


async def async_next(t: GraphTraversal):
    return await wrap_future(t.promise(lambda x: x.next()))


async def count_vertex_by_label(g: GraphTraversalSource):
    return await async_next(g.V().groupCount().by(__.label()))


async def count_edge_by_label(g: GraphTraversalSource):
    return await async_next(g.E().groupCount().by(__.label()))
