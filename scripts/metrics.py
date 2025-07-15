from numpy import number
import traci
import networkx as nx

from concurrent.futures import ThreadPoolExecutor
from networkx.algorithms.connectivity import local_node_connectivity

# from concurrent.futures import ProcessPoolExecutor

PA_LIFESPAN = {}
LAST_POSITIONS = {}

def calcula_metricas_para_ap(ap, G_base, components, positions, betweenness, degree, closeness, eigenvector):

    local_metricas = {
        "betweenness": betweenness.get(ap, 0),
        "degree": degree.get(ap, 0),
        "closeness": closeness.get(ap, 0),
        "eigenvector": eigenvector.get(ap, 0),
        "lifespan": PA_LIFESPAN.get(ap, 1),
        "mobility": 0,
        "fragmentation_impact": 0,
        "k_connectivity": 0,
    }

    if ap in LAST_POSITIONS:
        x0, y0 = LAST_POSITIONS[ap]
        x1, y1 = positions[ap]
        dx, dy = x1 - x0, y1 - y0
        local_metricas["mobility"] += (dx**2 + dy**2)**0.5

    # Atualiza LAST_POSITIONS
    LAST_POSITIONS[ap] = positions[ap]

    # Cópia do grafo para evitar conflitos
    G = G_base.copy()
    vizinhos = list(G.neighbors(ap))
    G.remove_node(ap)
    local_metricas["fragmentation_impact"] = nx.number_connected_components(G) - components

    # Restaura o grafo para k-connectivity
    G.add_node(ap)
    for vizinho in vizinhos:
        G.add_edge(ap, vizinho)

    local_metricas["k_connectivity"] = min(
        local_node_connectivity(G, ap, v) for v in G.nodes if v != ap
    )

    return local_metricas

def calcular_metricas_paralela(G, positions) -> tuple[dict, list]:

    """
        Calcula métricas médias para pontos de articulação:
        Betweenness Centrality
        Degree Centrality
        Closeness Centrality,
        Eigenvector Centrality,
        Tempo de vida,
        Mobilidade relativa,
        Impacto na fragmentação,
        K-connectivity local,
        Graph Density,
        Number of cars,
    """

    articulation_points = list(nx.articulation_points(G))
    n = len(articulation_points)

    # Atualiza tempo de vida
    for ap in articulation_points:
        PA_LIFESPAN[ap] = PA_LIFESPAN.get(ap, 0) + 1

    metrics = {
        "betweenness": 0.0,
        "degree": 0.0,
        "closeness": 0.0,
        "eigenvector": 0.0,
        "lifespan": 0.0,
        "mobility": 0.0,
        "fragmentation_impact": 0.0,
        "k_connectivity": 0.0,
        "density": nx.density(G) * 100 * n,
        "number_of_cars": G.number_of_nodes() * n,
        "articulation_points": articulation_points
    }

    if n == 0: return (metrics, [])

    geoPosAPs = []

    for ap in articulation_points:
        x, y = positions[ap]
        lon, lat = traci.simulation.convertGeo(x, y)
        geoPosAPs.append((lat, lon))

    # Métricas globais do grafo
    betweenness = nx.betweenness_centrality(G)
    degree = dict(G.degree())
    closeness = nx.closeness_centrality(G)
    components = nx.number_connected_components(G)

    try:
        eigenvector = nx.eigenvector_centrality(G, max_iter=500)
    except nx.PowerIterationFailedConvergence:
        eigenvector = {node: 0 for node in G.nodes()}

    # Rodar paralelamente
    with ThreadPoolExecutor() as executor:
        resultados = executor.map(
            lambda ap: calcula_metricas_para_ap(ap, G, components, positions, betweenness, degree, closeness, eigenvector),
            articulation_points
        )

    for r in resultados:
        for k in r:
            metrics[k] += r[k]

    # Média das métricas
    for m in metrics:
        if m != "density" and m != "number_of_cars" and m != "articulation_points":
            metrics[m] /= n

    return (metrics, geoPosAPs)

def metrics_builder(n, number_of_nodes):
    return {
        "len_articulation_points": n,
        "articulation_points_percentage": n / number_of_nodes * 100,
        "betweenness": 0.0,
        "degree": 0.0,
        "closeness": 0.0,
        "eigenvector": 0.0,
        "lifespan": 0.0,
        "mobility": 0.0,
        "fragmentation_impact": 0.0,
        "k_connectivity": 0.0,
    }

def calcular_metricas(list_veiculos, G, positions, multithreaded = False) -> tuple[list[dict], list]:

    # if (multithreaded):
    #     return calcular_metricas_paralela(G, positions)

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

    global_articulation_points = list(nx.articulation_points(G))
    len_global_APs: int = len(global_articulation_points)

    global_metrics = {
        "len_articulation_points": len_global_APs,
        "articulation_points_percentage": len_global_APs / G.number_of_nodes() * 100,
        "betweenness": 0.0,
        "degree": 0.0,
        "closeness": 0.0,
        "eigenvector": 0.0,
        "lifespan": 0.0,
        "mobility": 0.0,
        "fragmentation_impact": 0.0,
        "k_connectivity": 0.0,
        "density": nx.density(G) * 100,
        "number_of_cars": G.number_of_nodes(),
        "articulation_points": global_articulation_points
    }

    if len_global_APs == 0: return ([global_metrics], [])

    metrics_list = []
    geoPosAPs = []

    # Métricas globais do grafo
    betweenness = nx.betweenness_centrality(G)
    degree = dict(G.degree())
    closeness = nx.closeness_centrality(G)
    components = nx.number_connected_components(G)

    try:
        eigenvector = nx.eigenvector_centrality(G, max_iter = 500)
    except nx.PowerIterationFailedConvergence:
        eigenvector = {node: 0 for node in G.nodes()}

    articulation_points_list = [global_articulation_points]

    value: str
    for value in list_veiculos.values():
        print(f"value: {value}")
        articulation_points = []
        for ap in global_articulation_points:
            if value == "AVL":
                if ap.startswith(value):
                    articulation_points.append(ap)
            else:
                if not ap.startswith(value):
                    articulation_points.append(ap)

        articulation_points_list.append(articulation_points)

    print(articulation_points_list)

    for articulation_points in articulation_points_list:

        # print(articulation_points)
        # print("len", len(articulation_points))

        n = len(articulation_points)

        metrics = {}


        if (articulation_points != global_articulation_points):
            metrics = metrics_builder(len(articulation_points), G.number_of_nodes())
        else:
            metrics = global_metrics

        metrics_list.append(metrics)
        if n == 0: continue

        for ap in articulation_points:

            # Atualiza posicao
            x, y = positions[ap]
            lon, lat = traci.simulation.convertGeo(x, y)
            geoPosAPs.append((lat, lon))

            # Atualiza tempo de vida
            PA_LIFESPAN[ap] = PA_LIFESPAN.get(ap, 0) + 1

            metrics["betweenness"] += betweenness.get(ap, 0)
            metrics["degree"] += degree.get(ap, 0)
            metrics["closeness"] += closeness.get(ap, 0)
            metrics["eigenvector"] += eigenvector.get(ap, 0)
            metrics["lifespan"] += PA_LIFESPAN.get(ap, 1)

            # Mobilidade relativa
            if ap in LAST_POSITIONS:
                x0, y0 = LAST_POSITIONS[ap]
                x1, y1 = positions[ap]
                dx, dy = x1 - x0, y1 - y0
                metrics["mobility"] += (dx ** 2 + dy ** 2) ** 0.5

            LAST_POSITIONS[ap] = positions[ap]

            # Remove temporariamente o nó
            vizinhos = list(G.neighbors(ap))
            G.remove_node(ap)

            metrics["fragmentation_impact"] += nx.number_connected_components(G) - components

            G.add_node(ap)
            for vizinho in vizinhos:
                G.add_edge(ap, vizinho)

            # metrics["k_connectivity"] += min(local_node_connectivity(G, ap, v) for v in G.nodes if v != ap)

        # Média das métricas
        for m in metrics:
            if m != "density" and m != "number_of_cars" and m != "len_articulation_points" and type(metrics[m]) != list:
                metrics[m] /= n

    if (metrics_list[0] == metrics_list[1]):
        print("(metrics_list[0] == metrics_list[1]) TRUE")
    else:
        print("(metrics_list[0] == metrics_list[1]) FALSE")

    if (metrics_list[0] == metrics_list[2]):
        print("(metrics_list[0] == metrics_list[2]) TRUE")
    else:
        print("(metrics_list[0] == metrics_list[2]) FALSE")

    if (metrics_list[1] == metrics_list[2]):
        print("(metrics_list[1] == metrics_list[2]) TRUE")
    else:
        print("(metrics_list[1] == metrics_list[2]) FALSE")

    return (metrics_list, geoPosAPs)
