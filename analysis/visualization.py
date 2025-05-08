import folium
import pandas as pd
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

def salvar_histograma(histogram):

    # Salvar histograma em CSV
    with open("output/histogram.csv", "w") as f:
        for t, (numAPs, numVertices, density) in enumerate(histogram):
            f.write(f"{t},{numAPs},{numVertices},{density:.2f}\n")

    # Carregar o CSV
    df = pd.read_csv("output/histogram.csv", names=["minute", "PA_count", "car_count", "density"])

    # Adicionar ponto final para 24:00 (opcional, só para o rótulo)
    last_row = pd.DataFrame([[1440, 0, 0, 0]], columns=["minute", "PA_count", "car_count", "density"])
    df = pd.concat([df, last_row], ignore_index=True)
    df["hour"] = df["minute"] // 60
    df["minute_of_hour"] = df["minute"] % 60
    df["time"] = df["hour"].astype(str).str.zfill(2) + ":" + df["minute_of_hour"].astype(str).str.zfill(2)

    # Definir rótulos no eixo X (um por hora)
    tick_indices = df[df["minute_of_hour"] == 0].index
    tick_labels = df.loc[tick_indices, "time"]

    # Criar figura e primeiro eixo (PA_count)
    fig, ax1 = plt.subplots(figsize=(15, 5))

    color1 = 'tab:blue'
    ax1.bar(df.index, df["PA_count"], color=color1, alpha=0.6, label="PA Count")
    ax1.set_xlabel("Horário")
    ax1.set_ylabel("Número de PAs", color=color1)
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.set_xticks(tick_indices)
    ax1.set_xticklabels(tick_labels, rotation=45)

    # Segundo eixo (densidade)
    ax2 = ax1.twinx()
    color2 = 'tab:red'
    ax2.plot(df.index, df["density"] * 100, color=color2, linewidth=2, label="Density (%)")
    ax2.set_ylabel("Densidade (%)", color=color2)
    ax2.tick_params(axis='y', labelcolor=color2)
    ax2.set_ylim(0, 100)

    # Terceiro eixo (car_count)
    ax3 = ax1.twinx()
    color3 = 'tab:green'
    ax3.spines["right"].set_position(("axes", 1.1))  # move o terceiro eixo mais para fora
    ax3.plot(df.index, df["car_count"], color=color3, linewidth=1.5, label="Car Count", linestyle='--')
    ax3.set_ylabel("Número de Carros", color=color3)
    ax3.tick_params(axis='y', labelcolor=color3)

    # Título e grid
    fig.suptitle("Histograma de Pontos de Articulação, Densidade e Número de Carros ao longo do dia")
    ax1.grid(True)
    fig.tight_layout()
    plt.savefig("output/histograma_pontos_articulacao.png")

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

