import os
from pathlib import Path
import traci

from abc import ABC, abstractmethod
from typing import override

from scripts.build_graph import build_graph, update_vehicle_positions

import networkx as nx
from networkx.algorithms.connectivity import local_node_connectivity

from scripts.utils import Timer
import scripts.visualization as vis

from scripts.utils import ap_geographical_position

class BaseMetricExtractor(ABC):

    G: nx.Graph = nx.Graph()
    subscribed_vehicles = set()
    progress_bar = None

    PA_LIFESPAN, LAST_POSITIONS = {}, {}
    DISTANCE_THRESHOLD: int
    USE_QUAD_TREE: bool | tuple
    METRICS_EVERY_N_SECONDS: int
    DEBUGGING: bool
    HEADER_CREATED: bool = False

    METRICAS_MAP = {
        "betweenness": ["Normalized Mean", "Average AP Betweenness Centrality"],
        "degree": ["Mean Degree", "Average AP Node Degree"],
        "closeness": ["Normalized Mean", "Average AP Closeness Centrality"],
        "eigenvector": ["Normalized Mean", "Average AP Eigenvector Centrality"],
        "lifespan": ["Time (s)", "Average AP Lifespan"],
        "mobility": ["Percentage (%)", "Average AP Mobility"],
        "fragmentation_impact": ["Normalized Value", "Fragmentation Impact"],
        "k_connectivity": ["Integer (k)", "K-Connectivity"],
        "number_of_articulation_points": ["Number of Articulation Points", "Number of Articulation Points"],
        "articulation_points_percentage": ["Articulation Points (%)", "Proportion of Articulation Points among Vehicles"],
        "density": ["Density (%)", "Graph Density"],
        "number_of_cars": ["Quantity", "Number of Cars in the Graph"],
    }

    def __init__(self, distance_threshold, use_quad_tree, metrics_every_n_seconds, debuggin, progress_bar) -> None:

        super().__init__()

        self.progress_bar = progress_bar

        self.DISTANCE_THRESHOLD = distance_threshold
        self.USE_QUAD_TREE = use_quad_tree
        self.METRICS_EVERY_N_SECONDS = metrics_every_n_seconds
        self.DEBUGGING = debuggin

    @abstractmethod
    def extract_data(self, step: float, G = None) -> None: pass

    @abstractmethod
    def save_data(self, outputPath: str, access_mode: str = "w") -> None: pass

    def get_last_saved_step(self, nome_arquivo):

        with open(nome_arquivo, "rb+") as f:  # leitura/escrita binária

            f.seek(0, 2)  # vai pro final do arquivo

            pos = f.tell() - 1

            # pula quebras de linha no fim do arquivo
            while pos >= 0:
                f.seek(pos)
                if f.read(1) != b"\n":
                    break
                pos -= 1

            # agora volta até encontrar a quebra de linha anterior
            while pos >= 0:
                f.seek(pos)
                if f.read(1) == b"\n":
                    break
                pos -= 1

            # lê a última linha e converte para string
            ultima_linha = f.readline().decode("utf-8").rstrip("\n")
            # print(f"ultima_linha: {ultima_linha}")

            # divide por vírgulas e retorna o primeiro elemento
            partes = ultima_linha.split(",")
            return partes[0] if partes else "0"

    @abstractmethod
    def save_csv(self, outputPath, PC_ID: int, NUM_PCS: int) -> None: pass

    def _save_csv(self, metrics, metrics_map, outputPath, PC_ID: int, NUM_PCS: int) -> None:

        outputPath += "histogram.csv"

        file_exists = Path(outputPath).exists()

        # Salvar histograma
        with open(outputPath, "a" if file_exists else "w") as file:

            if not self.HEADER_CREATED:

                csv_header = ["time"]

                for key in metrics_map:
                    csv_header.append(key)
                self.HEADER_CREATED = True

                file.write(",".join(csv_header) + "\n")

            current_step: int
            try:
                current_step = int(self.get_last_saved_step(outputPath)) + NUM_PCS
            except Exception:
                current_step = PC_ID

            values = [f"{current_step}"] + [f"{metrics[metric_key]:.4g}" for metric_key in metrics_map]
            file.write(",".join(values) + "\n")

    @abstractmethod
    def get_debug_data(self) -> dict: pass

    def _get_debug_data(self) -> dict:

        debug_data = {}

        if self.G.number_of_nodes() > 0:
            debug_data["Vertices"] = self.G.number_of_nodes()
            debug_data["APs"] = len(list(nx.articulation_points(self.G)))
            debug_data["Edges"] = self.G.number_of_edges()
            debug_data["Density"] = f"{nx.density(self.G) * 100:.2f}%"

        else:
            debug_data["cars"] = len(traci.vehicle.getIDList())

        return debug_data

    """
    Calcula métricas médias para pontos de articulação:
        Betweenness Centrality,
        Degree Centrality,
        Closeness Centrality,
        Eigenvector Centrality,
        Tempo de vida,
        Mobilidade relativa,
        Impacto na fragmentação,
        K-connectivity local,
        Graph Density,
        Number of cars
    """
    def _extract_data(self, articulation_points, last_positions = LAST_POSITIONS, pa_lifespan = PA_LIFESPAN):

        n: int = len(articulation_points)

        geographical_positions = []

        metrics = {
            "betweenness"                   : 0.0,
            "degree"                        : 0.0,
            "closeness"                     : 0.0,
            "eigenvector"                   : 0.0,
            "lifespan"                      : 0.0,
            "mobility"                      : 0.0,
            "fragmentation_impact"          : 0.0,
            "k_connectivity"                : 0.0,
            "number_of_articulation_points" : n,
            "articulation_points_percentage": n / self.G.number_of_nodes() * 100,
            "density"                       : nx.density(self.G) * 100,
            "number_of_cars"                : self.G.number_of_nodes(),
            "articulation_points"           : articulation_points,
        }

        if n == 0: return metrics, geographical_positions

        timers = {
            "betweenness"                    : Timer(),
            "degree"                         : Timer(),
            "closeness"                      : Timer(),
            "eigenvector"                    : Timer(),
            "lifespan"                       : Timer(),
            "mobility"                       : Timer(),
            "fragmentation_impact"           : Timer(),
            "k_connectivity"                 : Timer(),
            "number_of_connected_components" : Timer(),
        }

        if self.DEBUGGING: print("Começando eigenvector")
        timers["eigenvector"].start()
        try:
            eigenvector = nx.eigenvector_centrality(self.G, max_iter = 500)
        except nx.PowerIterationFailedConvergence:
            eigenvector = {node: 0 for node in self.G.nodes()}
        timers["eigenvector"].end()
        if self.DEBUGGING: print(f"Time taken to calculate eigenvector: {timers['eigenvector']}")

        if self.DEBUGGING: print("Começando closeness")
        timers["closeness"].start()
        closeness   = nx.closeness_centrality(self.G)
        timers["closeness"].end()
        if self.DEBUGGING: print(f"Time taken to calculate closeness: {timers['closeness']}")

        if self.DEBUGGING: print("Começando betweenness")
        timers["betweenness"].start()
        betweenness = nx.betweenness_centrality(self.G)
        timers["betweenness"].end()
        if self.DEBUGGING: print(f"Time taken to calculate betweenness: {timers['betweenness']}")

        if self.DEBUGGING: print("Começando number_of_connected_components")
        timers["number_of_connected_components"].start()
        components  = nx.number_connected_components(self.G)
        timers["number_of_connected_components"].end()
        if self.DEBUGGING: print(f"Time taken to calculate number_of_connected_components: {timers['number_of_connected_components']}")

        for ap in articulation_points:

            pa_lifespan[ap] = pa_lifespan.get(ap, 0) + 1

            if self.DEBUGGING: print("Começando betweenness")
            timers["betweenness"].start()
            metrics["betweenness"]          += betweenness[ap]
            timers["betweenness"].end()
            if self.DEBUGGING: print(f"Time taken to calculate betweenness: {timers['betweenness']}")

            if self.DEBUGGING: print("Começando degree")
            timers["degree"].start()
            metrics["degree"]               += self.G.degree(ap)
            timers["degree"].end()
            if self.DEBUGGING: print(f"Time taken to calculate degree: {timers['degree']}")

            if self.DEBUGGING: print("Começando closeness")
            timers["closeness"].start()
            metrics["closeness"]            += closeness[ap]
            timers["closeness"].end()
            if self.DEBUGGING: print(f"Time taken to calculate closeness: {timers['closeness']}")

            if self.DEBUGGING: print("Começando eigenvector")
            timers["eigenvector"].start()
            metrics["eigenvector"]          += eigenvector[ap]
            timers["eigenvector"].end()
            if self.DEBUGGING: print(f"Time taken to calculate eigenvector: {timers['eigenvector']}")

            if self.DEBUGGING: print("Começando lifespan")
            timers["lifespan"].start()
            metrics["lifespan"]             += pa_lifespan[ap]
            timers["lifespan"].end()
            if self.DEBUGGING: print(f"Time taken to calculate lifespan: {timers['lifespan']}")

            if self.DEBUGGING: print("Começando mobility")
            timers["mobility"].start()
            metrics["mobility"]             += self.relative_mobility(ap, last_positions)
            timers["mobility"].end()
            if self.DEBUGGING: print(f"Time taken to calculate mobility: {timers['mobility']}")

            if self.DEBUGGING: print("Começando fragmentation_impact")
            timers["fragmentation_impact"].start()
            metrics["fragmentation_impact"] += self.fragmentation_impact(ap) - components
            timers["fragmentation_impact"].end()
            if self.DEBUGGING: print(f"Time taken to calculate fragmentation_impact: {timers['fragmentation_impact']}")

            if self.DEBUGGING: print("Começando k_connectivity")
            timers["k_connectivity"].start()
            metrics["k_connectivity"]       += min(local_node_connectivity(self.G, ap, v) for v in self.G.nodes if v != ap)
            timers["k_connectivity"].end()
            if self.DEBUGGING: print(f"Time taken to calculate k_connectivity: {timers['k_connectivity']}")

            geographical_positions.append(self.G.nodes[ap]["pos"])

        self._calculate_average(metrics, n)

        if self.DEBUGGING: print("---------------------------------------------------")

        return metrics, geographical_positions

    # def ap_geographical_position(self, pos: tuple):
    #     x, y = pos
    #     lon, lat = traci.simulation.convertGeo(x, y)
    #     return (lat, lon)

    def relative_mobility(self, articulation_point: str, last_positions: dict):

        result = 0

        if articulation_point in last_positions:

            x0, y0 = last_positions[articulation_point]
            x1, y1 = self.G.nodes[articulation_point]["pos"]
            dx, dy = x1 - x0, y1 - y0

            result = (dx ** 2 + dy ** 2) ** 0.5

        last_positions[articulation_point] = self.G.nodes[articulation_point]["pos"]

        return result

    def fragmentation_impact(self, ap: str):

        vizinhos = list(self.G.neighbors(ap))
        position = self.G.nodes[ap]["pos"]
        self.G.remove_node(ap)

        number_of_connected_components = nx.number_connected_components(self.G)

        self.G.add_node(ap, pos=position)
        for vizinho in vizinhos:
            self.G.add_edge(ap, vizinho)

        return number_of_connected_components

    def _calculate_average(self, metrics: dict, n: int) -> None:

        # NOTE: DRY Violated!
        lista = {
            "betweenness",
            "degree",
            "closeness",
            "eigenvector",
            "lifespan",
            "mobility",
            "fragmentation_impact",
            "k_connectivity",
        }

        for m in metrics:
            if m in lista:
                metrics[m] /= n

class SimpleExtractor(BaseMetricExtractor):

    metrics_data = []
    geographical_positions = []

    def __init__(self, distance_threshold, use_quad_tree, metrics_every_n_seconds, debugging, progress_bar) -> None:
        super().__init__(distance_threshold, use_quad_tree, metrics_every_n_seconds, debugging, progress_bar)

    @override
    def extract_data(self, step: float, G = None) -> None:

        if step % self.METRICS_EVERY_N_SECONDS != 0: return

        if G == None:
            positions = update_vehicle_positions(self.subscribed_vehicles)
            self.G = build_graph(positions, self.DISTANCE_THRESHOLD, self.USE_QUAD_TREE)
        else:
            self.G = G

        if (self.progress_bar):
            self.progress_bar.set_postfix(self.get_debug_data())

        articulation_points = list(nx.articulation_points(self.G))

        metrics, coordenates = self._extract_data(articulation_points)
        self.metrics_data.append(metrics)
        self.geographical_positions.append(coordenates)

    @override
    def save_data(self, outputPath: str, access_mode: str = "w") -> None:

        os.makedirs(outputPath, exist_ok = True)

        vis.generate_histograms(self.metrics_data, outputPath, self.METRICAS_MAP, access_mode)
        vis.generate_heat_map(self.geographical_positions, outputPath)

    @override
    def get_debug_data(self) -> dict:
        return self._get_debug_data()

    # if self.current_step % self.METRICS_EVERY_N_SECONDS != 0 or len(self.metrics_data) == 0:
        #     return self.debug_data

        # return self._get_debug_data(self.metrics_data[-1])

class AdvancedExtractor(BaseMetricExtractor):

    global_metrics_data, cars_metrics_data, buses_metrics_data = [], [], []
    global_geo_pos, cars_geo_pos, buses_geo_pos = [], [], []

    GLOBAL_PA_LIFESPAN, GLOBAL_LAST_POSITIONS = {}, {}
    BUSES_PA_LIFESPAN, BUSES_LAST_POSITIONS = {}, {}
    CARS_PA_LIFESPAN, CARS_LAST_POSITIONS = {}, {}

    def __init__(self, distance_threshold, use_quad_tree, metrics_every_n_seconds, debugging, progress_bar) -> None:
        super().__init__(distance_threshold, use_quad_tree, metrics_every_n_seconds, debugging, progress_bar)

    @override
    def extract_data(self, step: float, G = None) -> None:

        if step % self.METRICS_EVERY_N_SECONDS != 0: return

        if G == None:
            positions = update_vehicle_positions(self.subscribed_vehicles)
            lat_lon = {key: ap_geographical_position(value) for key, value in positions.items()}
            self.G = build_graph(positions, lat_lon, self.DISTANCE_THRESHOLD, self.USE_QUAD_TREE)
            vis.draw_graph_with_real_positions(self.G, draw_radius=True)
        else:
            self.G = G

        if (self.progress_bar):
            self.progress_bar.set_postfix(self.get_debug_data())

        global_articulation_points = list(nx.articulation_points(self.G))

        articulation_points_cars, articulation_points_buses = [], []

        ap: str
        for ap in global_articulation_points:
            if ap.startswith("AVL"):
                articulation_points_buses.append(ap)
            else:
                articulation_points_cars.append(ap)

        # NOTE:
        # Pensar na possibilidade de usar @decorator para resolver o problema das variaveis "globais"
        # LAST_POSITIONS, PA_LIFESPAN

        metrics, coordenates = self._extract_data(global_articulation_points, self.GLOBAL_LAST_POSITIONS, self.GLOBAL_PA_LIFESPAN)
        self.global_metrics_data.append(metrics)
        self.global_geo_pos.append(coordenates)

        buses_metrics, coordenates = self._extract_data(articulation_points_buses, self.BUSES_LAST_POSITIONS, self.BUSES_PA_LIFESPAN)
        self.buses_metrics_data.append(buses_metrics)
        self.buses_geo_pos.append(coordenates)

        cars_metrics, coordenates = self._extract_data(articulation_points_cars, self.CARS_LAST_POSITIONS, self.CARS_PA_LIFESPAN)
        self.cars_metrics_data.append(cars_metrics)
        self.cars_geo_pos.append(coordenates)

    @override
    def save_data(self, outputPath: str, access_mode: str = "w") -> None:

        os.makedirs(outputPath, exist_ok = True)

        vis.generate_histograms(self.global_metrics_data, outputPath + "global_", self.METRICAS_MAP, access_mode)
        vis.generate_histograms(self.buses_metrics_data, outputPath + "buses_", self.METRICAS_MAP, access_mode)
        vis.generate_histograms(self.cars_metrics_data, outputPath + "cars_", self.METRICAS_MAP, access_mode)

        vis.generate_heat_map(self.global_geo_pos, outputPath + "global_")
        vis.generate_heat_map(self.buses_geo_pos, outputPath + "buses_")
        vis.generate_heat_map(self.cars_geo_pos, outputPath + "cars_")

    @override
    def save_csv(self, outputPath, PC_ID: int, NUM_PCS: int) -> None:
        self._save_csv(self.global_metrics_data[-1], self.METRICAS_MAP, outputPath, PC_ID, NUM_PCS)
        self._save_csv(self.cars_metrics_data[-1], self.METRICAS_MAP, outputPath, PC_ID, NUM_PCS)
        self._save_csv(self.buses_metrics_data[-1], self.METRICAS_MAP, outputPath, PC_ID, NUM_PCS)

    @override
    def get_debug_data(self) -> dict:

        return self._get_debug_data()

    # if self.current_step % self.METRICS_EVERY_N_SECONDS != 0 or len(self.global_metrics_data) == 0:
        #     return self._get_debug_data()

        # return self._get_debug_data(self.global_metrics_data[-1])

def extractor_factory(trace_type, distance_threshold = 100, use_quad_tree: tuple | bool = False, metrics_every_n_seconds: int = 60, debugging: bool = False, progress_bar = None) -> BaseMetricExtractor:

    if trace_type in { "santa_tereza", "sao_paulo" }:
        return SimpleExtractor(distance_threshold, use_quad_tree, metrics_every_n_seconds, debugging, progress_bar)

    if trace_type in { "luxembourg", "monaco" }:
        return AdvancedExtractor(distance_threshold, use_quad_tree, metrics_every_n_seconds, debugging, progress_bar)

    raise ValueError(f"Unsupported trace_type: {trace_type}")
