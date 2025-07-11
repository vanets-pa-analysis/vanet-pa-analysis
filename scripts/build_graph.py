import traci
import networkx as nx

import matplotlib.pyplot as plt

from scripts.quad_tree import Rectangle
from scripts.quad_tree import QuadTreeNode

def build_quad_tree(positions, bounds, distance_threshold):

    vehicles = list(positions.keys())

    min_range = distance_threshold

    x = bounds["xmin"] + bounds["xmax"] / 2
    y = bounds["ymin"] + bounds["ymax"] / 2
    w = bounds["xmax"] - bounds["xmin"] / 2
    h = bounds["ymax"] - bounds["ymin"] / 2

    root = QuadTreeNode(Rectangle(x, y, w, h), min_range)

    for i in range(0, len(vehicles)):

        x, y = positions[vehicles[i]]

        root.insert(Rectangle(x, y, min_range, min_range, id=vehicles[i]))

    return root

def build_graph_with_qt(positions, distance_threshold, bounds) -> nx.Graph:

    qt = build_quad_tree(positions, bounds, distance_threshold)

    G = nx.Graph()

    vehicles = list(positions.keys())
    min_range = distance_threshold

    for i in range(len(vehicles)):

        vi, (ix, iy) = vehicles[i], positions[vehicles[i]]
        G.add_node(vi)

        for vj in qt.search(Rectangle(ix, iy, min_range, min_range, id=vi)):

            jx, jy = positions[vj.id]
            dx = ix - jx
            dy = iy - jy

            if (dx**2 + dy**2)**0.5 <= distance_threshold and vi != vj.id:
                G.add_edge(vi, vj.id)

    return G

def build_graph(positions, distance_threshold, use_quadTree = (False, {})) -> nx.Graph:

    if (use_quadTree[0]):
        return build_graph_with_qt(positions, distance_threshold, use_quadTree[1])

    G = nx.Graph()

    vehicles = list(positions.keys())

    for i in range(len(vehicles)):

        vi, pi = vehicles[i], positions[vehicles[i]]
        G.add_node(vi)

        for j in range(i + 1, len(vehicles)):

            vj, pj = vehicles[j], positions[vehicles[j]]
            dx = pi[0] - pj[0]
            dy = pi[1] - pj[1]

            if (dx ** 2 + dy ** 2) ** 0.5 <= distance_threshold:
                G.add_edge(vi, vj)

    return G

def draw_graph_with_real_positions(G, positions, save_path=None, show=True, draw_radius=False, radius=100):

    """
    Desenha o grafo com os nós posicionados em suas coordenadas reais (x, y),
    com a opção de desenhar um raio ao redor de cada nó.

    Parâmetros:
        G (networkx.Graph): O grafo com os veículos como nós.
        positions (dict): Dicionário {vehicle_id: (x, y)} com posições dos veículos.
        save_path (str): Caminho para salvar a imagem (opcional).
        show (bool): Se True, exibe a imagem. Se False, apenas salva (se save_path for definido).
        draw_radius (bool): Se True, desenha círculos de raio `radius` ao redor de cada nó.
        radius (float): O raio em metros para os círculos.
    """
    plt.figure(figsize=(10, 10))

    # Desenha o grafo com posições reais
    nx.draw(
        G,
        pos=positions,
        node_size=30,
        node_color='blue',
        edge_color='gray',
        with_labels=True
    )

    # Desenha círculos de raio ao redor dos nós
    if draw_radius:
        ax = plt.gca()
        for x, y in positions.values():
            circle = plt.Circle((x, y), radius, color='red', fill=False, linestyle='--', linewidth=0.5)
            ax.add_patch(circle)

    plt.xlabel("X (metros)")
    plt.ylabel("Y (metros)")
    plt.title("Vehicle Graph with Real Positions")
    plt.axis("equal")

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    if show:
        plt.show()
    else:
        plt.close()

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
