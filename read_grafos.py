from pathlib import Path

from tqdm import tqdm as progress_bar

from natsort import natsorted

import scripts.utils as utils

import networkx as nx
from networkx.readwrite.gpickle import read_gpickle

from scripts.metrics_extractor import extractor_factory

###################################################

TRACE_NAME         = "luxembourg"
DISTANCE_THRESHOLD = "100"
SIM_ID             = 3
DEBUGGING          = False
TOTAL_TIME         = 10000
CALCULATE_METRICS  = True
SAVE_RESULTS       = True

###################################################

def main():

    metrics_extractor = extractor_factory(trace_type=TRACE_NAME, debugging=DEBUGGING,)

    # input_path = Path(f"saved_graphs/simulation_{utils.getNextSimID("saved_graphs")}_{TRACE_NAME}_{(END_TIME):.0f}s_{DISTANCE_THRESHOLD}m/")
    input_path = Path(f"saved_graphs/simulation_{SIM_ID}_{TRACE_NAME}_{TOTAL_TIME}s_{DISTANCE_THRESHOLD}m")

    files = list(input_path.glob("*.gpickle"))
    files = natsorted(files, key=lambda p: p.name)

    for file_path in progress_bar(files, desc="Reading Graphs", unit="graph"):

        G: nx.Graph = read_gpickle(file_path)

        if DEBUGGING:
            print(f"Loaded graph from: {file_path}")
            print(f"Number of nodes: {G.number_of_nodes()}")
            print(f"Number of edges: {G.number_of_edges()}")

        if CALCULATE_METRICS:
           metrics_extractor.extract_data(0, G)

    if SAVE_RESULTS:
        outputPath = f"output/simulation_{utils.getNextSimID()}_{TRACE_NAME}_{TOTAL_TIME:.0f}s_{DISTANCE_THRESHOLD}m/"
        metrics_extractor.save_data(outputPath)

    print("SUCCESS!!!!!")

if __name__ == "__main__": main()
