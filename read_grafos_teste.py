from pathlib import Path

from tqdm import tqdm as progress_bar

from natsort import natsorted

import scripts.utils as utils

import networkx as nx

from scripts.metrics_extractor import extractor_factory
from scripts.visualization import draw_graph_with_real_positions

###################################################

TRACE_NAME         = "luxembourg"
DISTANCE_THRESHOLD = "100"
SIM_ID             = 5
DEBUGGING          = True
TOTAL_TIME         = 86400
CALCULATE_METRICS  = True
SAVE_RESULTS       = True

###################################################

def main():

    metrics_extractor = extractor_factory(trace_type=TRACE_NAME, debugging=DEBUGGING,)

    # input_path = Path(f"saved_graphs/simulation_{utils.getNextSimID("saved_graphs")}_{TRACE_NAME}_{(END_TIME):.0f}s_{DISTANCE_THRESHOLD}m/")
    # input_path = Path(f"E:/simulation_{SIM_ID}_{TRACE_NAME}_{TOTAL_TIME}s_{DISTANCE_THRESHOLD}m")
    input_path = Path(f"/mnt/e/simulation_{SIM_ID}_{TRACE_NAME}_{TOTAL_TIME}s_{DISTANCE_THRESHOLD}m")

    if not input_path.exists() or not input_path.is_dir():
        print("Path:", input_path)
        print("Exists:", input_path.exists())
        print("Is Dir:", input_path.is_dir())
        exit(-1)

    files = list(input_path.glob("*.gpickle"))
    files = natsorted(files, key=lambda p: p.name)

    print("lendo grafo")
    largest_graph_filepath: Path = files[-100]
    largest_graph: nx.Graph = nx.read_gpickle(largest_graph_filepath)
    print("terminou de ler grafo")

    # draw_graph_with_real_positions(largest_graph)

    # for file_path in progress_bar(files, desc="Reading Graphs", unit="graph"):

    #     G: nx.Graph = nx.read_gpickle(file_path)

    #     if G.number_of_nodes() > largest_graph.number_of_nodes():
    #         largest_graph = G
    #         largest_graph_filepath = file_path

    # print(f"largest_graph_filepath: {largest_graph_filepath}")

    if DEBUGGING:
        print(f"Loaded graph from: {largest_graph_filepath}")
        print(f"Number of nodes: {largest_graph.number_of_nodes()}")
        print(f"Number of edges: {largest_graph.number_of_edges()}")
        print(f"Number of AP: {len(list(nx.articulation_points(largest_graph)))}")

        # if len(list(nx.articulation_points(largest_graph))):
        #     print(f"Latitude e longitude de um qualquer", largest_graph.nodes[list(nx.articulation_points(largest_graph))[0]]["pos"])

    if CALCULATE_METRICS:
       metrics_extractor.extract_data(0, largest_graph)

    if SAVE_RESULTS:
        outputPath = f"output/simulation_{utils.getNextSimID()}_{TRACE_NAME}_{TOTAL_TIME:.0f}s_{DISTANCE_THRESHOLD}m/"
        metrics_extractor.save_data(outputPath)

    print("Metrics successfully extracted!")

if __name__ == "__main__": main()
