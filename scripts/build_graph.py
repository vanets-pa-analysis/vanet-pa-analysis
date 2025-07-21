import traci
import networkx as nx

import matplotlib.pyplot as plt

from scripts.quad_tree import Rectangle
from scripts.quad_tree import QuadTreeNode

def euclidean_distance(dx, dy):
    return (dx ** 2 + dy ** 2) ** 0.5

def build_quad_tree(positions, bounds, distance_threshold):

    x = bounds["xmin"] + bounds["xmax"] / 2
    y = bounds["ymin"] + bounds["ymax"] / 2
    w = bounds["xmax"] - bounds["xmin"] / 2
    h = bounds["ymax"] - bounds["ymin"] / 2

    root = QuadTreeNode(Rectangle(x, y, w, h), distance_threshold)

    for vehicle in positions.keys():
        x, y = positions[vehicle]
        root.insert(Rectangle(x, y, distance_threshold, distance_threshold, id=vehicle))

    return root

def build_graph_with_qt(positions, attribute, distance_threshold, bounds) -> nx.Graph:

    qt = build_quad_tree(positions, bounds, distance_threshold)

    G = nx.Graph()

    for vi in positions:

        G.add_node(vi, pos=attribute[vi])


        ix, iy = positions[vi]

        for vj in qt.search(Rectangle(ix, iy, distance_threshold, distance_threshold, id=vi)):

            jx, jy = positions[vj.id]
            dx, dy = ix - jx, iy - jy

            if euclidean_distance(dx, dy) <= distance_threshold and vi != vj.id:
                G.add_edge(vi, vj.id)

    return G

def build_graph(positions, attribute, distance_threshold, use_quadTree = (False, {})) -> nx.Graph:

    if (use_quadTree[0]):
        return build_graph_with_qt(positions, attribute, distance_threshold, use_quadTree[1])

    G = nx.Graph()

    vehicles = list(positions.keys())

    for i, vi in enumerate(vehicles):

        G.add_node(vi, pos=attribute[vi])
        
        ix, iy = positions[vi]

        for j in range(i + 1, len(vehicles)):

            vj = vehicles[j]

            jx, jy = positions[vj]
            dx, dy = ix - jx, iy - jy

            if euclidean_distance(dx, dy) <= distance_threshold and vi != vj:
                G.add_edge(vi, vj)

    return G

def update_vehicle_positions(subscribed_vehicles: set) -> dict:

    current_vehicle_ids = set(traci.vehicle.getIDList())
    new_vehicles = current_vehicle_ids - subscribed_vehicles

    for vid in new_vehicles:
        traci.vehicle.subscribe(vid, (traci.constants.VAR_POSITION,))

    subscribed_vehicles |= new_vehicles

    results = traci.vehicle.getAllSubscriptionResults()

    return {
        vehicle_id: results[vehicle_id][traci.constants.VAR_POSITION]
        for vehicle_id in results
        if traci.constants.VAR_POSITION in results[vehicle_id]
    }

# def compare_graphs(G1, G2):

#     if nx.is_isomorphic(G1, G2):
#         print("Ambos os grafos são iguais")
#     else:
#         compare_graphs(G1, G2)
#         qt.print()
#         draw_graph_with_real_positions(G2, positions, draw_radius=True)
#         draw_graph_with_real_positions(G1, positions, draw_radius=True)

def compare_graphs(G1, G2):

    print("Comparando grafos...")
    print(f"G1: {G1.number_of_nodes()} nós, {G1.number_of_edges()} arestas")
    print(f"G2: {G2.number_of_nodes()} nós, {G2.number_of_edges()} arestas")

    nodes_diff = set(G1.nodes) ^ set(G2.nodes)

    if nodes_diff:
        print("Diferença de nós:", nodes_diff)
    else:
        print("Os grafos têm os mesmos nós.")

    edges1 = set(G1.edges)
    edges2 = set(G2.edges)

    only_in_G1 = edges1 - edges2
    only_in_G2 = edges2 - edges1

    if only_in_G1:
        print(f"Arestas em G1 mas não em G2 ({len(only_in_G1)}): {only_in_G1}")
    if only_in_G2:
        print(f"Arestas em G2 mas não em G1 ({len(only_in_G2)}): {only_in_G2}")

    if not nodes_diff and not only_in_G1 and not only_in_G2:
        print("Os grafos são idênticos.")
