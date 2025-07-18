import os
import traci

from abc import ABC, abstractmethod
from typing import override

from scripts.build_graph import build_graph, update_vehicle_positions

import networkx as nx
from networkx.algorithms.connectivity import local_node_connectivity

import scripts.visualization as vis

class BaseMetricExtractor(ABC):

    G: nx.Graph = nx.Graph()
    subscribed_vehicles = set()
    progress_bar = None

    PA_LIFESPAN, LAST_POSITIONS = {}, {}
    DISTANCE_THRESHOLD: int
    USE_QUAD_TREE: bool | tuple
    METRICS_EVERY_N_SECONDS: int
    DEBUGGING: bool

    METRICAS_MAP = {
        "betweenness": ["Normalized Mean", "Average AP Betweenness Centrality"],
        "degree": ["Mean Degree", "Average AP Node Degree"],
        "closeness": ["Normalized Mean", "Average AP Closeness Centrality"],
        "eigenvector": ["Normalized Mean", "Average AP Eigenvector Centrality"],
        "lifespan": ["Time (s)", "Average AP Lifespan"],
        "mobility": ["Percentage (%)", "Average AP Mobility"],
        "fragmentation_impact": ["Normalized Value", "Fragmentation Impact"],
        # "k_connectivity": ["Integer (k)", "K-Connectivity"],
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
    def save_data(self, outputPath: str) -> None: pass

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

        try:
            eigenvector = nx.eigenvector_centrality(self.G, max_iter = 500)
        except nx.PowerIterationFailedConvergence:
            eigenvector = {node: 0 for node in self.G.nodes()}

        betweenness = nx.betweenness_centrality(self.G)
        closeness   = nx.closeness_centrality(self.G)
        components  = nx.number_connected_components(self.G)

        for ap in articulation_points:

            pa_lifespan[ap] = pa_lifespan.get(ap, 0) + 1

            metrics["betweenness"]          += betweenness[ap]
            metrics["degree"]               += self.G.degree(ap)
            metrics["closeness"]            += closeness[ap]
            metrics["eigenvector"]          += eigenvector[ap]
            metrics["lifespan"]             += pa_lifespan[ap]
            metrics["mobility"]             += self.relative_mobility(ap, last_positions)
            metrics["fragmentation_impact"] += self.fragmentation_impact(ap) - components
            # metrics["k_connectivity"]       += min(local_node_connectivity(self.G, ap, v) for v in self.G.nodes if v != ap)

            # geographical_positions.append(self.ap_geographical_position(self.G.nodes[ap]["pos"]))

        self._calculate_average(metrics, n)

        return metrics, geographical_positions

    def ap_geographical_position(self, pos: tuple):
        x, y = pos
        lon, lat = traci.simulation.convertGeo(x, y)
        return (lat, lon)

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
        # self.geographical_positions.append(coordenates)

    @override
    def save_data(self, outputPath: str) -> None:
        os.makedirs(outputPath, exist_ok = True)
        vis.generate_histograms(self.metrics_data, outputPath, self.METRICAS_MAP)

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
            self.G = build_graph(positions, self.DISTANCE_THRESHOLD, self.USE_QUAD_TREE)
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
        # self.global_geographical_positions.append(coordenates)

        buses_metrics, coordenates = self._extract_data(articulation_points_buses, self.BUSES_LAST_POSITIONS, self.BUSES_PA_LIFESPAN)
        self.buses_metrics_data.append(buses_metrics)
        # self.buses_geographical_positions.append(coordenates)

        cars_metrics, coordenates = self._extract_data(articulation_points_cars, self.CARS_LAST_POSITIONS, self.CARS_PA_LIFESPAN)
        self.cars_metrics_data.append(cars_metrics)
        # self.cars_geographical_positions.append(coordenates)

    @override
    def save_data(self, outputPath: str) -> None:

        os.makedirs(outputPath, exist_ok = True)

        vis.generate_histograms(self.global_metrics_data, outputPath + "global_", self.METRICAS_MAP)
        vis.generate_histograms(self.buses_metrics_data, outputPath + "buses_", self.METRICAS_MAP)
        vis.generate_histograms(self.cars_metrics_data, outputPath + "cars_", self.METRICAS_MAP)

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
