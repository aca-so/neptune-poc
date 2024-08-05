from gremlin_python.process.graph_traversal import GraphTraversalSource, __


def count_vertex_by_label(g: GraphTraversalSource):
    return g.V().groupCount().by(__.label()).next()


def count_edge_by_label(g: GraphTraversalSource):
    return g.E().groupCount().by(__.label()).next()
