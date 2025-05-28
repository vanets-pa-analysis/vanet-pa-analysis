import traci
import networkx as nx
import os

from analysis.articulation import find_articulation_points
from analysis.visualization import generate_heat_map
from analysis.visualization import generate_all_histograms 

DEBUGGING = True
SUMO_BINARY = "sumo-gui"  # ou "sumo-gui" se quiser ver
# TRACE_NAME = "santa_tereza"
TRACE_NAME = "sao_paulo"
NET_FILE = f"net/{TRACE_NAME}.net.xml"
ROUTE_FILE = f"routes/{TRACE_NAME}.rou.xml"
SIMULATION_MAX_TIME = 3600

DISTANCE_THRESHOLD = 100  # metros

def getNextSimID():

    path = "output/lastSimulationID.txt"

    # Read the current ID
    with open(path, "r") as f:
        lastSimID = int(f.read())

    # Increment the ID
    lastSimID += 1

    # Overwrite with the new ID
    with open(path, "w") as f:
        f.write(str(lastSimID))

    return lastSimID

def get_vehicle_positions():

    positions = {}

    for vid in traci.vehicle.getIDList():
        x, y = traci.vehicle.getPosition(vid)
        positions[vid] = (x, y)

    return positions

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

def main():

    traci.start([SUMO_BINARY, "-n", NET_FILE, "-r", ROUTE_FILE])
    step = 0
    csvData = []
    geoPosAPs = []

    sum = 0

    while traci.simulation.getMinExpectedNumber() > 0 and step < SIMULATION_MAX_TIME:

        traci.simulationStep()
        positions = get_vehicle_positions()

        G = build_graph(positions)

        sum += G.number_of_nodes()

        aps = find_articulation_points(G)
        # metricas = calcular_metricas(aps, G, positions)
        metricas = {}

        if DEBUGGING:
            print(f"Number of edges: {G.number_of_edges()}")
            print(f"Number of nodes: {G.number_of_nodes()}")
            print(f"Graph Density: {nx.density(G) * 100:.2f}%")
            print(f"[t={step}s] {len(aps)} articulation points")
            print("-----------------------------")

        # Salvar estatísticas
        csvData.append((len(aps), metricas))

        for vehicle in aps:
            x, y = positions[vehicle]
            lon, lat = traci.simulation.convertGeo(x, y)
            geoPosAPs.append((lat, lon))

        step += 1

        # if len(aps) > 20:
        #     print(aps)
        #     nx.draw(G, with_labels=True)  # Desenha com rótulos nos nós
        #     plt.show()

    print(f"Avg cars on the map {sum / step}")

    traci.close()

    outputPath = f"output/simulation_{getNextSimID()}_{TRACE_NAME}_{step}s_{DISTANCE_THRESHOLD}m/"

    os.makedirs(outputPath, exist_ok=True)

    generate_all_histograms(csvData, outputPath)
    generate_heat_map(geoPosAPs, outputPath)

if __name__ == "__main__":
    main()
