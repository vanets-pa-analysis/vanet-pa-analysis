import folium
import pandas as pd
import os
import matplotlib.pyplot as plt

from folium.plugins import HeatMap

def generate_heat_map(geoPosAPs):

    """
    Gera um mapa de calor com base na lista de coordenadas (latitude, longitude)
    dos pontos de articulação.
    """

    # Coordenadas centrais aproximadas de Belo Horizonte
    bh_center = [-19.919, -43.935]

    # Criar o mapa
    m = folium.Map(location=bh_center, zoom_start=14)

    # Adicionar o heatmap diretamente da lista
    HeatMap(geoPosAPs, radius=10, blur=15, max_zoom=1).add_to(m)

    # Salvar o HTML interativo
    m.save("output/heatmap_pa.html")

def generate_all_histograms(outputPath):

    df = pd.read_csv(outputPath)

    # Converter tempo em formato legível
    df["hour"] = df["tempo"] // 60
    df["minute_of_hour"] = df["tempo"] % 60
    df["time"] = df["hour"].astype(str).str.zfill(2) + ":" + df["minute_of_hour"].astype(str).str.zfill(2)

    metricas = [
        "quantidadePAs", "betweenness", "degree", "closeness", "eigenvector",
        "lifespan", "mobility", "fragmentationImpact", "kConnectivity"
    ]

    os.makedirs("output/histogramas", exist_ok=True)

    for metrica in metricas:
        plt.figure(figsize=(15, 5))
        plt.plot(df["time"], df[metrica], linewidth=1.2)
        plt.title(f"{metrica} ao longo do tempo")
        plt.xlabel("Horário")
        plt.ylabel(metrica)
        plt.xticks(df["time"][::60], rotation=45)
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f"output/histogramas/{metrica}.png")
        plt.close()

# def generate_histogram(outputPath):
#
#     # Carregar apenas as duas primeiras colunas, ignorando o cabeçalho
#     df = pd.read_csv(outputPath, usecols=[0, 1], skiprows=1, names=["minute", "PA_count"])
#
#     # Garantir que 'minute' é inteiro
#     df["minute"] = df["minute"].astype(int)
#
#     # Converter minutos para horário
#     df["hour"] = df["minute"] // 60
#     df["minute_of_hour"] = df["minute"] % 60
#     df["time"] = df["hour"].astype(str).str.zfill(2) + ":" + df["minute_of_hour"].astype(str).str.zfill(2)
#
#     # Plotar
#     plt.figure(figsize=(15, 5))
#     plt.plot(df["time"], df["PA_count"], linewidth=1.2, color="darkblue")
#     plt.title("Quantidade de Pontos de Articulação (PA) ao longo do dia")
#     plt.xlabel("Horário")
#     plt.ylabel("Quantidade de PAs")
#     plt.xticks(df["time"][::60], rotation=45)  # mostra só 1 ponto por hora
#     plt.grid(True)
#     plt.tight_layout()
#     plt.savefig("output/histograma_pontos_articulacao.png")
#

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

