from os import mkdir
from pathlib import Path

from tqdm import tqdm as progress_bar

from natsort import natsorted

import scripts.utils as utils

import networkx as nx

from scripts.metrics_extractor import extractor_factory

###################################################

TRACE_NAME            = "luxembourg"
DISTANCE_THRESHOLD    = "100"
SIM_ID                = 5
DEBUGGING             = False
TOTAL_TIME            = 86400
CALCULATE_METRICS     = True
SAVE_RESULTS          = True
WRITE_THROUGH         = SAVE_RESULTS and True
NUM_PCS               = 60
PC_ID                 = 1
GRAFOS_JA_PROCESSADOS = 0

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

    files = files[GRAFOS_JA_PROCESSADOS:]

    file_number = -1

    outputPath: str = ""

    if SAVE_RESULTS:
        outputPath = f"output/simulation_{utils.getNextSimID()}_{TRACE_NAME}_{TOTAL_TIME:.0f}s_{DISTANCE_THRESHOLD}m/"
        mkdir(outputPath)

    for file_path in progress_bar(files, desc="Reading Graphs", unit="graph"):

        file_number += 1

        if file_number % NUM_PCS != PC_ID: continue

        G: nx.Graph = utils.read_gpickle(file_path)

        if DEBUGGING:
            print(f"Loaded graph from: {file_path}")
            print(f"Number of nodes: {G.number_of_nodes()}")
            print(f"Number of AP: {len(list(nx.articulation_points(G)))}")
            print(f"Number of edges: {G.number_of_edges()}")

            if len(list(nx.articulation_points(G))):
                print(f"Latitude e longitude de um qualquer", G.nodes[list(nx.articulation_points(G))[0]]["pos"])

        if CALCULATE_METRICS:
           metrics_extractor.extract_data(0, G)

        if WRITE_THROUGH:
            metrics_extractor.save_csv(outputPath, PC_ID, NUM_PCS)

    if SAVE_RESULTS:
        metrics_extractor.save_data(outputPath)

    print("Metrics successfully extracted!")

if __name__ == "__main__": main()
