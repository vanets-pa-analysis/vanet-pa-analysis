import networkx as nx

def find_articulation_points(G):
    return list(nx.articulation_points(G))
