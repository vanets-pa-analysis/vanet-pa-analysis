import traci
# import sumolib
import networkx as nx

from analysis.articulation import find_articulation_points
from analysis.visualization import generate_heat_map
from analysis.visualization import salvar_histograma

# import os

SUMO_BINARY = "sumo"  # ou "sumo-gui" se quiser ver
NET_FILE = "net/bh.net.xml"
ROUTE_FILE = "routes/bh.rou.xml"

DISTANCE_THRESHOLD = 100  # metros

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

def main():

    traci.start([SUMO_BINARY, "-n", NET_FILE, "-r", ROUTE_FILE])
    step = 0
    histogram = []
    geoPosAPs = []

    sum = 0

    while traci.simulation.getMinExpectedNumber() > 0:

        traci.simulationStep()
        positions = get_vehicle_positions()

        numberOfCars = len(list(positions.keys()))
        sum += numberOfCars

        G = build_graph(positions)

        print(f"Number of edges: {G.number_of_edges()}")
        print(f"Number of nodes: {G.number_of_nodes()}")
        print(f"Graph Density: {nx.density(G) * 100:.2f}%")

        aps = find_articulation_points(G)
        # print(f"Number of Articulation Points: {len(aps)}")

        # Salvar estatísticas
        histogram.append(len(aps))

        for vehicle in aps:
            x, y = positions[vehicle]
            lon, lat = traci.simulation.convertGeo(x, y)
            geoPosAPs.append((lat, lon))

        print(f"[t={step}s] {len(aps)} articulation points")

        # (Opcional) Salvar as posições dos APs com coordenadas
        # Aqui você poderia salvar em um CSV para o mapa de calor depois

        step += 1

        print("-----------------------------")

    print(f"Avg cars on the map {sum / step}")

    traci.close()

    salvar_histograma(histogram)
    generate_heat_map(geoPosAPs)

if __name__ == "__main__":
    main()

# NOTE: Alternativa para exportar o histograma

# # Carregar o CSV
# df = pd.read_csv("output/histogram.csv", names=["minute", "PA_count"])
#
# # Converter minutos para horário (opcional, mas fica mais legível)
# df["hour"] = df["minute"] // 60
# df["minute_of_hour"] = df["minute"] % 60
# df["time"] = df["hour"].astype(str).str.zfill(2) + ":" + df["minute_of_hour"].astype(str).str.zfill(2)
#
# # Plotar
# plt.figure(figsize=(15, 5))
# plt.plot(df["time"], df["PA_count"], linewidth=1.2, color="darkblue")
# plt.title("Quantidade de Pontos de Articulação (PA) ao longo do dia")
# plt.xlabel("Horário")
# plt.ylabel("Quantidade de PAs")
# plt.xticks(df["time"][::60], rotation=45)  # mostra só 1 ponto por hora
# plt.grid(True)
# plt.tight_layout()
# plt.show()
