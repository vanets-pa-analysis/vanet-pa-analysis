import folium
import pandas as pd
import os
import matplotlib.pyplot as plt

from folium.plugins import HeatMap

def generate_heat_map(geoPosAPs, outputPath):

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
    m.save(outputPath + "heatmap_pa.html")

def save_csv(outputPath, csvData):

    outputPath += "histogram.csv"

    # Salvar histograma
    with open(outputPath, "w") as f:

        f.write("tempo,quantidadePAs,betweenness,degree,closeness,eigenvector,lifespan,mobility,fragmentationImpact,kConnectivity,density,number_of_cars\n")

        for tempo, (qtdPAs, metricas) in enumerate(csvData):
            valores = [f"{tempo}", f"{qtdPAs}"] + [f"{value:.4f}" for value in metricas]
            f.write(",".join(valores) + "\n")

    return outputPath

def generate_all_histograms(csvData, outputPath):

    csvFile = save_csv(outputPath, csvData)

    df = pd.read_csv(csvFile)

    # Converter tempo em formato legível
    df["hour"] = df["tempo"] // 60
    df["minute_of_hour"] = df["tempo"] % 60
    df["time"] = df["hour"].astype(str).str.zfill(2) + ":" + df["minute_of_hour"].astype(str).str.zfill(2)

    # NOTE: metricas["metrica"][0] -> Unidade de Medida
    # NOTE: metricas["metrica"][1] -> Nome para o título do gráfico

    """
        Betweenness, Closeness e Eigenvector Centrality geralmente são valores normalizados entre 0 e 1 (ou em média por nó), então indiquei como média normalizada.

        Degree: média dos graus dos nós — "Média de Grau".

        Lifespan: suponho que seja o tempo de permanência de um nó (ex: veículo) no grafo — "Tempo (s)".

        Mobility: dado que vem de simulações SUMO, é comum representar mobilidade como porcentagem de movimento/alcance — "Porcentagem (%)".

        Fragmentation Impact: medida adimensional usada para avaliar o impacto da fragmentação — "Valor Normalizado".

        K-Connectivity: nível de conectividade k do grafo, é um número inteiro.

        Number of Cars: contador direto — "Quantidade".
    """

    metricas = {
        "quantidadePAs": ["Number of Articulation Points", "Number of Articulation Points"],
        "density": ["Density (%)", "Graph Density"],
        "betweenness": ["Normalized Mean", "Average AP Betweenness Centrality"],
        "degree": ["Mean Degree", "Average AP Node Degree"],
        "closeness": ["Normalized Mean", "Average AP Closeness Centrality"],
        "eigenvector": ["Normalized Mean", "Average AP Eigenvector Centrality"],
        "lifespan": ["Time (s)", "Average AP Lifespan"],
        "mobility": ["Percentage (%)", "Average AP Mobility"],
        "fragmentationImpact": ["Normalized Value", "Fragmentation Impact"],
        "kConnectivity": ["Integer (k)", "K-Connectivity"],
        "number_of_cars": ["Quantity", "Number of Cars in the Graph"],
    }

    outputPath += "histograms"
    os.makedirs(outputPath, exist_ok=True)

    for metrica in metricas:
        plt.figure(figsize=(15, 5))
        plt.plot(df["time"], df[metrica], linewidth=1.2)
        plt.title(f"{metricas[metrica][1]} over time")
        plt.xlabel("Horário")
        plt.ylabel(metricas[metrica][0])
        plt.xticks(df["time"][::60], rotation=45)
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f"{outputPath}/{metrica}.png")
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
