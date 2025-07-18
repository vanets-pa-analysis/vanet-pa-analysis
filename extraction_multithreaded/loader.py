from pathlib import Path

from networkx.readwrite.gpickle import read_gpickle

import networkx as nx

from tqdm import tqdm as progress_bar

import multiprocessing as mp
import threading

from scripts.metrics_extractor import BaseMetricExtractor

class Loader:

    # Sentinel to tell workers to shut down
    SENTINEL = None

    def __init__(self, folder_path: str, metrics_extractor: BaseMetricExtractor, cpu_cores: int) -> None:

        # Set this based on the number of cores of your CPU
        self.NUM_WORKERS = cpu_cores

        self.metrics_extractor = metrics_extractor

        # Folder with .gpickle files
        self.folder_path = Path(folder_path)
        self.file_list = sorted(self.folder_path.glob("*.gpickle"))

        # Use a multiprocessing Queue for cross-process communication
        self.graph_queue = mp.Queue(maxsize=2 * self.NUM_WORKERS) # Only some preloaded graphs in memory

    def extract_data(self):

        # Start loader in a thread
        loader_thread = threading.Thread(target=self.loader)
        loader_thread.start()

        # Start multiple processors
        workers = []
        for i in range(self.NUM_WORKERS):
            p = mp.Process(target=self.processor, args=(self, i))
            p.start()
            workers.append(p)

        # Wait for all
        loader_thread.join()
        for p in workers: p.join()

    def loader(self):

        for file in progress_bar(self.file_list, desc="Extracting Data", unit="graph"):
            G: nx.Graph = read_gpickle(file)
            self.graph_queue.put((file.name, G))

        for _ in range(self.NUM_WORKERS):
            self.graph_queue.put(self.SENTINEL)

    def processor(self, worker_id):

        while True:

            item = self.graph_queue.get()

            if item is self.SENTINEL: break

            filename, G = item

            print(f"[Worker {worker_id}] Processing {filename} with {G.number_of_nodes()} nodes")
            self.metrics_extractor.extract_data(0, G, {})
