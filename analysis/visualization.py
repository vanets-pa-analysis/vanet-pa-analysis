import folium
import pandas as pd
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

# def generate_heat_map(geoPosAPs):
#
#     # Carregar os dados
#     df = pd.read_csv("output/pa_coordinates.csv")
#
#     # Criar o mapa centralizado em BH
#     bh_center = [-19.919, -43.935]  # ajuste conforme necessário
#     m = folium.Map(location=bh_center, zoom_start=14)
#
#     # Adicionar o heatmap
#     heat_data = [[row["lat"], row["lon"]] for index, row in df.iterrows()]
#     HeatMap(heat_data, radius=10, blur=15, max_zoom=1).add_to(m)
#
#     # Salvar como HTML interativo
#     m.save("output/heatmap_pa.html")

def salvar_histograma(histogram):

    # Salvar histograma
    with open("output/histogram.csv", "w") as f:
        for t, count in enumerate(histogram):
            f.write(f"{t},{count}\n")

    data = pd.read_csv("output/histogram.csv", header=None, names=["t", "count"])
    plt.plot(data["t"], data["count"])
    plt.title("Número de Pontos de Articulação ao Longo do Tempo")
    plt.xlabel("Tempo (s)")
    plt.ylabel("Qtd de PAs")
    plt.grid(True)
    # plt.show()
    plt.savefig("output/histograma_pontos_articulacao.png")
