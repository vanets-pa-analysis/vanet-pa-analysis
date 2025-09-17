import os
import folium
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt

from numbers import Number
from folium.plugins import HeatMap

import networkx as nx
import matplotlib.pyplot as plt
import pyproj

def draw_graph_with_real_positions(G: nx.Graph, save_path=None, show=True, draw_radius=False, radius=100):
    """
    Desenha o grafo com os nós posicionados em suas coordenadas reais (lat, lon),
    convertendo para coordenadas em metros para escala correta.

    Parâmetros:
        G (networkx.Graph): O grafo com os veículos como nós.
        save_path (str): Caminho para salvar a imagem (opcional).
        show (bool): Se True, exibe a imagem. Se False, apenas salva (se save_path for definido).
        draw_radius (bool): Se True, desenha círculos de raio `radius` ao redor de cada nó.
        radius (float): O raio em metros para os círculos.
    """
    plt.figure(figsize=(10, 10))

    # Extrair lat/lon
    latlon_positions = {v: G.nodes[v]["pos"] for v in G.nodes()}

    # Converter para coordenadas projetadas (em metros) usando pyproj
    # Aqui usamos WGS84 -> UTM automático baseado na posição média
    lats = [lat for lat, lon in latlon_positions.values()]
    lons = [lon for lat, lon in latlon_positions.values()]
    mean_lat, mean_lon = sum(lats) / len(lats), sum(lons) / len(lons)

    # Definir projeção UTM baseada no centro
    utm_zone = int((mean_lon + 180) // 6) + 1
    proj = pyproj.Proj(proj="utm", zone=utm_zone, ellps="WGS84")

    projected_positions = {
        v: proj(lon, lat)  # (x, y) em metros
        for v, (lat, lon) in latlon_positions.items()
    }

    # Desenha o grafo com coordenadas em metros
    nx.draw(
        G,
        pos=projected_positions,
        node_size=30,
        node_color='blue',
        edge_color='gray',
        with_labels=True
    )

    # Desenha círculos de raio ao redor dos nós
    if draw_radius:
        ax = plt.gca()
        for x, y in projected_positions.values():
            circle = plt.Circle((x, y), radius, color='red', fill=False, linestyle='--', linewidth=0.5)
            ax.add_patch(circle)

    plt.xlabel("X (metros)")
    plt.ylabel("Y (metros)")
    plt.title("Vehicle Graph with GPS Positions (converted to meters)")
    plt.axis("equal")

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    if show:
        plt.show()
    else:
        plt.close()

def generate_heat_map(geoPosAPs, outputPath):

    """
        Gera um mapa de calor com base na lista de coordenadas (latitude, longitude)
        dos pontos de articulação.
    """

    flattened_coordinates = [coordinate for coordinate_list in geoPosAPs for coordinate in coordinate_list]

    # Calcular centro dinâmico baseado nas coordenadas dos pontos
    if flattened_coordinates:
        latitudes = [coord[0] for coord in flattened_coordinates]
        longitudes = [coord[1] for coord in flattened_coordinates]

        # Centro baseado na média das coordenadas
        center_lat = sum(latitudes) / len(latitudes)
        center_lon = sum(longitudes) / len(longitudes)
        dynamic_center = [center_lat, center_lon]

        # Calcular zoom apropriado baseado na dispersão dos pontos
        lat_range = max(latitudes) - min(latitudes)
        lon_range = max(longitudes) - min(longitudes)
        max_range = max(lat_range, lon_range)

        # Ajustar zoom baseado na dispersão (quanto maior a dispersão, menor o zoom)
        if max_range > 1.0:
            zoom_level = 10
        elif max_range > 0.5:
            zoom_level = 11
        elif max_range > 0.1:
            zoom_level = 12
        elif max_range > 0.05:
            zoom_level = 13
        else:
            zoom_level = 14
    else:
        # Fallback para Belo Horizonte se não houver coordenadas
        dynamic_center = [-19.919, -43.935]
        zoom_level = 14

    # Criar o mapa
    m = folium.Map(location=dynamic_center, zoom_start=zoom_level)



    # Adicionar o heatmap usando as coordenadas achatadas
    if flattened_coordinates:
        HeatMap(flattened_coordinates, radius=10, blur=15, max_zoom=1).add_to(m)

    # Salvar o HTML interativo
    m.save(outputPath + "heatmap_pa.html")

def save_csv(metrics, outputPath, metrics_map, access_mode = "w"):

    outputPath += "histogram.csv"

    # Salvar histograma
    with open(outputPath, access_mode) as file:

        csv_header = ["time"]

        for key in metrics_map:
            csv_header.append(key)

        file.write(",".join(csv_header) + "\n")

        for time, m in enumerate(metrics):
            values = [f"{time}"] + [f"{m[metric_key]:.4g}" for metric_key in metrics_map]
            file.write(",".join(values) + "\n")

    return outputPath

def generate_histograms(metrics, output_path, metrics_map, access_mode: str = "w"):

    csv_file_path = save_csv(metrics, output_path, metrics_map, access_mode)
    df = pd.read_csv(csv_file_path)

    # Converter time em formato legível
    df["hour"] = df["time"] // 60
    df["minute_of_hour"] = df["time"] % 60
    df["time"] = df["hour"].astype(str).str.zfill(2) + ":" + df["minute_of_hour"].astype(str).str.zfill(2)

    # NOTE: metricas["metrica"][0] -> Unidade de Medida
    # NOTE: metricas["metrica"][1] -> Nome para o título do gráfico

    output_path += "histograms"
    os.makedirs(output_path, exist_ok=True)

    for metrica in metrics_map:
        plt.figure(figsize=(15, 5))
        plt.plot(df["time"], df[metrica], linewidth=1.2)
        plt.title(f"{metrics_map[metrica][1]} over time")
        plt.xlabel("Horário")
        plt.ylabel(metrics_map[metrica][0])
        plt.xticks(df["time"][::60], rotation=45)
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f"{output_path}/{metrica}.png")
        plt.close()

# NOTE: Jeito alternativo de salvar o Histograma

# def salvar_histograma(histogram):
#
#     # Salvar histograma
#     with open("output/histogram.csv", "w") as f:
#         for t, count in enumerate(histogram):
#             f.write(f"{t},{count}\n")
#
#     data = pd.read_csv("output/histogram.csv", header=None, names=["t", "count"])
#     plt.plot(data["t"], data["count"])
#     plt.title("Número de Pontos de Articulação ao Longo do Tempo")
#     plt.xlabel("Tempo (s)")
#     plt.ylabel("Qtd de PAs")
#     plt.grid(True)
#     # plt.show()
#     plt.savefig("output/histograma_pontos_articulacao.png")
