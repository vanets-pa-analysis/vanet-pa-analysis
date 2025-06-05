import traci
import networkx as nx
<<<<<<< Updated upstream
import matplotlib.pyplot as plt
=======
import os
import subprocess
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

from quad_tree import Rectangle
from quad_tree import QuadTreeNode
>>>>>>> Stashed changes

from analysis.articulation import find_articulation_points
from analysis.visualization import generate_heat_map
from analysis.visualization import salvar_histograma

DEBUGGING = True
SUMO_BINARY = "sumo-gui"  # ou "sumo-gui" se quiser ver
<<<<<<< Updated upstream
NET_FILE = "net/santa_tereza.net.xml"
ROUTE_FILE = "routes/combined.rou.xml"
=======
TRACE_NAME = "santa_tereza"
# TRACE_NAME = "sao_paulo"
NET_FILE = f"net/{TRACE_NAME}.net.xml"
ROUTE_FILE = f"routes/{TRACE_NAME}.rou.xml"
SIMULATION_MAX_TIME = 24 * 60 * 60
DISTANCE_THRESHOLD = 100 # metros
METRICS_EVERY_N_SECONDS = 60 # once per simulated minute
>>>>>>> Stashed changes

# Dictionary-based definition of traffic periods
traffic_periods = {

    "night_cars": {
        "begin": 0,
        "end": 21600,
        "period": 5,
        "vtype": "car",
        "label": "00:00–06:00 (cars)",
        "color": "#f0f0f0"
    },

    "morning_rush_cars":  {
        "begin": 21600,
        "end": 36000,
        "period": 2,
        "vtype": "car",
        "label": "06:00–10:00 (cars)",
        "color": "#ffdede"
    },

    "morning_rush_buses": {
        "begin": 21600,
        "end": 36000,
        "period": 20,
        "vtype": "bus",
        "label": "06:00–10:00 (buses)",
        "color": "#ffdede"
    },

    "midday_cars": {
        "begin": 36000,
        "end": 57600,
        "period": 4,
        "vtype": "car",
        "label": "10:00–16:00 (cars)",
        "color": "#e0f7ff"
    },

    "midday_taxis": {
        "begin": 36000,
        "end": 57600,
        "period": 2,
        "vtype": "taxi",
        "label": "10:00–16:00 (taxis)",
        "color": "#e0f7ff"
    },

    "midday_buses": {
        "begin": 36000,
        "end": 57600,
        "period": 30,
        "vtype": "bus",
        "label": "10:00–16:00 (buses)",
        "color": "#e0f7ff"
    },

    "evening_rush_cars": {
        "begin": 57600,
        "end": 72000,
        "period": 2,
        "vtype": "car",
        "label": "16:00–20:00 (cars)",
        "color": "#ffdede"
    },

    "evening_rush_buses": {
        "begin": 57600,
        "end": 72000,
        "period": 20,
        "vtype": "bus",
        "label": "16:00–20:00 (buses)",
        "color": "#ffdede"
    },

    "late_evening_cars": {
        "begin": 72000,
        "end": 86400,
        "period": 5,
        "vtype": "car",
        "label": "20:00–24:00 (cars)",
        "color": "#f0f0f0"
    },
}

def prepare_route():

    # Prepare script lines from dictionary
    lines = []

    for i, (_, info) in enumerate(traffic_periods.items()):

        trip_file = f"routes/{TRACE_NAME}_{info['vtype']}_{i}.trips.xml"
        route_file = f"routes/{TRACE_NAME}_{info['vtype']}_{i}.rou.xml"
        lines.append(f"# {info['label']}")
        lines.append(
            f"python3 /usr/share/sumo/tools/randomTrips.py "
            f"-n {NET_FILE} "
            f"-o {trip_file} "
            f"-r {route_file} "
            f"--begin {info['begin']} --end {info['end']} "
            f"--period {info['period']} "
            f"--vtype {info['vtype']} "
            f"--prefix {info['vtype']}_{i}_ "
            f"--validate"
        )

    bash_script = "\n\n".join(lines)

    # Define the script path
    script_path = "bash/generate_routes.sh"

    # Write to file
    with open(script_path, "w") as f:
        f.write("#!/bin/bash\n\n")
        f.write(bash_script + "\n")

    # Make the script executable
    os.chmod(script_path, 0o755)

    # Optional: execute the script
    subprocess.run(["bash", script_path], check=True)

    print(f"Route generation script written and executed: {script_path}")

def merge_routes(output_path=f"routes/{TRACE_NAME}.rou.xml"):

    root = ET.Element("routes")
    vtype_set = set()  # Para evitar duplicatas de <vType>

    for i, (_, info) in enumerate(traffic_periods.items()):
        route_path = f"routes/{TRACE_NAME}_{info['vtype']}_{i}.rou.xml"
        if not os.path.exists(route_path):
            print(f"Arquivo não encontrado: {route_path}")
            continue

        tree = ET.parse(route_path)
        sub_root = tree.getroot()

        for elem in sub_root:
            if elem.tag == "vType":
                # Evitar duplicatas de vType com mesmo ID
                vtype_id = elem.attrib.get("id")
                if vtype_id in vtype_set:
                    continue
                vtype_set.add(vtype_id)

            root.append(elem)

    # Escrevendo o novo arquivo
    tree = ET.ElementTree(root)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tree.write(output_path, encoding="UTF-8", xml_declaration=True)
    print(f"Rotas mescladas salvas em: {output_path}")

def get_vehicle_positions():

    positions = {}

    for vid in traci.vehicle.getIDList():
        x, y = traci.vehicle.getPosition(vid)
        positions[vid] = (x, y)

    return positions

def get_simulation_bounds(net_file_path=NET_FILE):
    """
    Extrai os limites espaciais da simulação (bounding box) do arquivo .net.xml.
    Retorna como um dicionário com xmin, ymin, xmax, ymax.
    """
    tree = ET.parse(net_file_path)
    root = tree.getroot()

    location = root.find("location")
    if location is not None and "convBoundary" in location.attrib:
        xmin, ymin, xmax, ymax = map(float, location.attrib["convBoundary"].split(','))
        return {
            "xmin": xmin,
            "ymin": ymin,
            "xmax": xmax,
            "ymax": ymax
        }
    else:
        raise ValueError("Não foi possível encontrar a boundary no arquivo .net.xml.")

def build_quad_tree(positions, bounds):
    
    vehicles = list(positions.keys())

    min_range = DISTANCE_THRESHOLD

    x = bounds["xmin"] + bounds["xmax"] / 2
    y = bounds["ymin"] + bounds["ymax"] / 2
    w = bounds["xmax"] - bounds["xmin"] / 2
    h = bounds["ymax"] - bounds["ymin"] / 2

    root = QuadTreeNode(Rectangle(x, y, w, h), min_range)

    for i in range(0, len(vehicles)):

        x, y = positions[vehicles[i]]

        root.insert(Rectangle(x, y, min_range, min_range, id=vehicles[i]))

    return root

def build_graph_with_qt(positions, bounds):

    qt = build_quad_tree(positions, bounds)

    G = nx.Graph()

    vehicles = list(positions.keys())
    min_range = DISTANCE_THRESHOLD

    for i in range(len(vehicles)):

        vi, (ix, iy) = vehicles[i], positions[vehicles[i]]
        G.add_node(vi)

        for vj in qt.search(Rectangle(ix, iy, min_range, min_range, id=vi)):

            jx, jy = positions[vj.id]
            dx = ix - jx
            dy = iy - jy

            if (dx**2 + dy**2)**0.5 <= DISTANCE_THRESHOLD and vi != vj.id:
                G.add_edge(vi, vj.id)

    return G

def build_graph(positions):

    G = nx.Graph()

    vehicles = list(positions.keys())

    for i in range(len(vehicles)):

        vi, pi = vehicles[i], positions[vehicles[i]]
        G.add_node(vi)

        for j in range(i + 1, len(vehicles)):

            vj, pj = vehicles[j], positions[vehicles[j]]
            dx = pi[0] - pj[0]
            dy = pi[1] - pj[1]

            if (dx**2 + dy**2)**0.5 <= DISTANCE_THRESHOLD:
                G.add_edge(vi, vj)

    return G

<<<<<<< Updated upstream
def main():

    traci.start([SUMO_BINARY, "-n", NET_FILE, "-r", ROUTE_FILE])
    step = 0
    SIM_STEP = 60  # segundos
    histogram = []
=======
PA_LIFESPAN = {}
LAST_POSITIONS = {}

def calcular_metricas(aps, G, positions):

    """
        Calcula métricas médias para pontos de articulação:
        Betweenness Centrality
        Degree Centrality
        Closeness Centrality,
        Eigenvector Centrality,
        Tempo de vida,
        Mobilidade relativa,
        Impacto na fragmentação,
        K-connectivity local,
        Graph Density,
        Number of cars,
    """

    n = len(aps)
    if n == 0:
        return [0.0] * 8

    # Atualiza tempo de vida
    for ap in aps:
        PA_LIFESPAN[ap] = PA_LIFESPAN.get(ap, 0) + 1

    metricas = {
        "betweenness": 0.0,
        "degree": 0.0,
        "closeness": 0.0,
        "eigenvector": 0.0,
        "lifespan": 0.0,
        "mobility": 0.0,
        "fragmentation_impact": 0.0,
        "k_connectivity": 0.0,
        "density": 0.0,
        "number_of_cars": 0.0,
    }

    # Métricas globais do grafo
    betweenness = nx.betweenness_centrality(G)
    degree = dict(G.degree())
    closeness = nx.closeness_centrality(G)

    try:
        eigenvector = nx.eigenvector_centrality(G, max_iter=500)
    except nx.PowerIterationFailedConvergence:
        eigenvector = {node: 0 for node in G.nodes()}

    for ap in aps:
        metricas["betweenness"] += betweenness.get(ap, 0)
        metricas["degree"] += degree.get(ap, 0)
        metricas["closeness"] += closeness.get(ap, 0)
        metricas["eigenvector"] += eigenvector.get(ap, 0)
        metricas["lifespan"] += PA_LIFESPAN.get(ap, 1)
        metricas["density"] = nx.density(G) * 100
        metricas["number_of_cars"] = G.number_of_nodes() 

        # Mobilidade relativa
        if ap in LAST_POSITIONS:
            x0, y0 = LAST_POSITIONS[ap]
            x1, y1 = positions[ap]
            dx, dy = x1 - x0, y1 - y0
            metricas["mobility"] += (dx**2 + dy**2)**0.5

        LAST_POSITIONS[ap] = positions[ap]

        # Fragmentação ao remover o PA
        G_temp = G.copy()
        G_temp.remove_node(ap)
        components = nx.number_connected_components(G_temp)
        metricas["fragmentation_impact"] += components

        # K-connectivity: grau mínimo entre vizinhos
        neighbors = list(G.neighbors(ap))
        if neighbors:
            local_degrees = [G.degree(n) for n in neighbors]
            metricas["k_connectivity"] += min(local_degrees)

    # Média das métricas
    return [metricas[k] / n for k in metricas]

def draw_graph_with_real_positions(G, positions, save_path=None, show=True, draw_radius=False, radius=DISTANCE_THRESHOLD):

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

def main():

    traci.start([SUMO_BINARY, "-n", NET_FILE, "-r", ROUTE_FILE])
    step = -1
    csvData = []
>>>>>>> Stashed changes
    geoPosAPs = []

    bounds = get_simulation_bounds()

    while traci.simulation.getMinExpectedNumber() > 0 and step < 1440:

<<<<<<< Updated upstream
        traci.simulationStep(step * SIM_STEP)
=======
        traci.simulationStep()

        step += 1

        if step % METRICS_EVERY_N_SECONDS != 0: continue

>>>>>>> Stashed changes
        positions = get_vehicle_positions()

        # G1 = build_graph(positions)
        G = build_graph_with_qt(positions, bounds)

        # if nx.is_isomorphic(G1, G2):
        #     print("Ambos os grafos são iguais")
        # else:
        #     compare_graphs(G1, G2)
        #     qt.print()
        #     draw_graph_with_real_positions(G2, positions, draw_radius=True)
        #     # draw_graph_with_real_positions(G1, positions, draw_radius=True)

        aps = find_articulation_points(G)
<<<<<<< Updated upstream

        if DEBUGGING:
            print(f"Number of edges: {G.number_of_edges()}")
            print(f"Number of nodes: {G.number_of_nodes()}")
            print(f"Graph Density: {nx.density(G) * 100:.2f}%")
            print(f"[Minute={step}] [Hour={int(step / 60)}] {len(aps)} articulation points")
            print("-----------------------------")

        # Salvar estatísticas
        histogram.append((len(aps), G.number_of_nodes(), nx.density(G)))
=======
        metricas = calcular_metricas(aps, G, positions)
>>>>>>> Stashed changes

        for vehicle in aps:
            x, y = positions[vehicle]
            lon, lat = traci.simulation.convertGeo(x, y)
            geoPosAPs.append((lat, lon))

        if DEBUGGING:
            print(f"Number of edges: {G.number_of_edges()}")
            print(f"Number of nodes: {G.number_of_nodes()}")
            print(f"Graph Density: {nx.density(G) * 100:.2f}%")
            # print(f"[time={step // 60 ** 2}h:{step // 60}m:{step}s]")
            print(f"[time={step // 60 ** 2}h:{step // 60}m:{step}s] {len(aps)} articulation points")
            print("-----------------------------")

        # Salvar estatísticas
        csvData.append((len(aps), metricas))

        if DEBUGGING and len(aps) > 21:
            print(aps)
            nx.draw(G, with_labels=True)  # Desenha com rótulos nos nós
            plt.show()

<<<<<<< Updated upstream
    print(f"Avg cars on the map {sum / step:.2f}")

=======
>>>>>>> Stashed changes
    traci.close()

    salvar_histograma(histogram)
    generate_heat_map(geoPosAPs)

if __name__ == "__main__":
    # prepare_route()
    # merge_routes()
    main()
