import traci

from abc import ABC, abstractmethod
from enum import Enum
from typing import override

import scripts.utils as utils

from scripts.build_graph import build_graph

import networkx as nx
from networkx.algorithms.connectivity import local_node_connectivity

class BaseMetricExtractor(ABC):

    G: nx.Graph
    positions: dict
    PA_LIFESPAN, LAST_POSITIONS = {}, {}
    DISTANCE_THRESHOLD: int
    USE_QUAD_TREE: bool | tuple
    METRICS_EVERY_N_SECONDS: int

    def __init__(self, DISTANCE_THRESHOLD, USE_QUAD_TREE, METRICS_EVERY_N_SECONDS) -> None:

        super().__init__()

        self.DISTANCE_THRESHOLD = DISTANCE_THRESHOLD
        self.USE_QUAD_TREE = USE_QUAD_TREE
        self.METRICS_EVERY_N_SECONDS = METRICS_EVERY_N_SECONDS

    @abstractmethod
    def extract_data(self, step: float) -> None: pass

    @abstractmethod
    def save_data(self) -> None: pass

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
    def _extract_data(self, articulation_points):

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
            "len_articulation_points"       : n,
            "articulation_points_percentage": int(n / self.G.number_of_nodes() * 100),
            "density"                       : int(nx.density(self.G) * 100),
            "number_of_cars"                : self.G.number_of_nodes(),
            "articulation_points"           : articulation_points,
        }

        if n == 0: return (metrics, geographical_positions)

        try:
            eigenvector = nx.eigenvector_centrality(self.G, max_iter = 500)
        except nx.PowerIterationFailedConvergence:
            eigenvector = {node: 0 for node in self.G.nodes()}

        betweenness = nx.betweenness_centrality(self.G)
        closeness   = nx.closeness_centrality(self.G)
        components  = nx.number_connected_components(self.G)

        for ap in articulation_points:

            self.PA_LIFESPAN[ap] = self.PA_LIFESPAN.get(ap, 0) + 1

            metrics["betweenness"]          += betweenness[ap]
            metrics["degree"]               += self.G.degree(ap)
            metrics["closeness"]            += closeness[ap]
            metrics["eigenvector"]          += eigenvector[ap]
            metrics["lifespan"]             += self.PA_LIFESPAN[ap]
            metrics["mobility"]             += self.relative_mobility(ap)
            metrics["fragmentation_impact"] += self.fragmentation_impact(ap) - components
            # metrics["k_connectivity"]       += min(local_node_connectivity(self.G, ap, v) for v in self.G.nodes if v != ap)

            geographical_positions.append(self.ap_geographical_position(ap))

        self._calculate_average(metrics, n)

        return (metrics, geographical_positions)

    def ap_geographical_position(self, articulation_point: str):
        x, y = self.positions[articulation_point]
        lon, lat = traci.simulation.convertGeo(x, y)
        return (lat, lon)

    def relative_mobility(self, articulation_point: str):

        self.LAST_POSITIONS[articulation_point] = self.positions[articulation_point]

        if articulation_point in self.LAST_POSITIONS:

            x0, y0 = self.LAST_POSITIONS[articulation_point]
            x1, y1 = self.positions[articulation_point]
            dx, dy = x1 - x0, y1 - y0

            return (dx ** 2 + dy ** 2) ** 0.5

        return 0

    def fragmentation_impact(self, ap: str):

        self.G.remove_node(ap)

        number_of_connected_components = nx.number_connected_components(self.G)

        self.G.add_node(ap)
        for vizinho in self.G.neighbors(ap):
            self.G.add_edge(ap, vizinho)

        return number_of_connected_components

    def _calculate_average(self, metrics: dict, n: int) -> None:
        for m in metrics:
            if type(metrics[m]) == float:
                metrics[m] /= n

class ConcreteClass1(BaseMetricExtractor):

    data = []
    geographical_positions = []

    def __init__(self, distance_threshold = 100, use_quad_tree: tuple | bool = False, metrics_every_n_seconds = 60) -> None:
        super().__init__(distance_threshold, use_quad_tree, metrics_every_n_seconds)

    @override
    def extract_data(self, step: float) -> None:

        if step % self.METRICS_EVERY_N_SECONDS != 0: return

        self.positions = utils.get_vehicle_positions()
        self.G = build_graph(self.positions, self.DISTANCE_THRESHOLD, self.USE_QUAD_TREE)

        articulation_points = list(nx.articulation_points(self.G))

        metrics, coordenates = self._extract_data(articulation_points)
        self.data.append(metrics)
        self.geographical_positions.append(coordenates)

    @override
    def save_data(self) -> None:
        print("Method 'save_data' is not yet implemented in ConcreteClass1")

class ConcreteClass2(BaseMetricExtractor):

    data = []
    geographical_positions = []

    def __init__(self, distance_threshold = 100, use_quad_tree: tuple | bool = False, metrics_every_n_seconds = 60) -> None:
        super().__init__(distance_threshold, use_quad_tree, metrics_every_n_seconds)

    @override
    def extract_data(self, step: float) -> None:

        if step % self.METRICS_EVERY_N_SECONDS != 0: return

        self.positions = utils.get_vehicle_positions()
        self.G = build_graph(self.positions, self.DISTANCE_THRESHOLD, self.USE_QUAD_TREE)

        global_articulation_points = nx.articulation_points(self.G)

        articulation_points_cars, articulation_points_buses = [], []

        ap: str
        for ap in global_articulation_points:
            if ap.startswith("AVL"):
                articulation_points_buses.append(ap)
            else:
                articulation_points_cars.append(ap)

        # metrics, coordenates = self._extract_data(articulation_points)
        # self.data.append(metrics)
        # self.geographical_positions.append(coordenates)

# class Extractors(Enum):
#     Extractor1 = ConcreteClass1,
#     Extractor2 = ConcreteClass2,

# def extractor_factory(trace_type, trace_data):
#     return trace_type.value()

# Salvar estatísticas
# metrics, coordenates = calcular_metricas(G, positions)
# geoPosAPs.append(coordenates)
# csv_data.append([m for m in metrics.values() if type(m) != list])

# if DEBUGGING: utils.debug_stats(G, step, metrics)


# outputPath = f"output/simulation_{utils.getNextSimID()}_{TRACE_NAME}_{(step - 1):.0f}s_{DISTANCE_THRESHOLD}m/"
# os.makedirs(outputPath, exist_ok = True)

# vis.generate_histograms(csv_data, outputPath)
# vis.generate_heat_map(geoPosAPs, outputPath)
