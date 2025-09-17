import pickle
import networkx as nx
import xml.etree.ElementTree as ET
import traci, time

class Timer:
    def __init__(self):
        self._start = None
        self._end = None

    def start(self):
        self._start = time.perf_counter()
        self._end = None  # Reset end in case the same timer is reused

    def end(self):
        if self._start is None:
            raise RuntimeError("Timer has not been started.")
        self._end = time.perf_counter()

    def time(self):
        if self._start is None:
            raise RuntimeError("Timer has not been started.")
        if self._end is None:
            # If timer hasn't been stopped, measure until now
            return time.perf_counter() - self._start
        return self._end - self._start

    def __str__(self) -> str:
        return f"{self.time():.6f}"

def getNextSimID(path = "output"):

    path += "/last_simulation_ID.txt"

    # Read the current ID
    with open(path, "r") as f:
        lastSimID = int(f.read())

    # Increment the ID
    lastSimID += 1

    # Overwrite with the new ID
    with open(path, "w") as f:
        f.write(str(lastSimID))

    return lastSimID

def ap_geographical_position(pos: tuple):
        x, y = pos
        lon, lat = traci.simulation.convertGeo(x, y)
        return (lat, lon)

def get_end_time(sumocfg_path) -> int:

    tree = ET.parse(sumocfg_path)
    root = tree.getroot()

    for time_tag in root.findall("time"):

        end = time_tag.find("end")

        if end is not None:
            return int(end.attrib["value"])

    FULL_DAY = 60 * 60 * 24

    return FULL_DAY

def get_begin_time(sumocfg_path) -> int:

    tree = ET.parse(sumocfg_path)
    root = tree.getroot()

    for time_tag in root.findall("time"):

        begin = time_tag.find("begin")

        if begin is not None:
            return int(begin.attrib["value"])

    return 0

def extract_net_path(sumocfg_path: str) -> str:
    """
    Parses a SUMO .sumocfg file and returns the network file path (.net.xml).

    Raises:
        FileNotFoundError: If the config file doesn't exist.
        ET.ParseError: If the XML is malformed.
        ValueError: If required tags or attributes are missing.

    Returns:
        str: The value of the 'net-file' attribute.
    """
    tree = ET.parse(sumocfg_path)
    root = tree.getroot()

    input_section = root.find('input')
    if input_section is None:
        raise ValueError("Missing <input> section in the SUMO config file.")

    net_file = input_section.find('net-file')
    if net_file is None:
        raise ValueError("Missing <net-file> tag in the <input> section.")

    net_path = net_file.attrib.get('value')
    if not net_path:
        raise ValueError("<net-file> tag is missing the 'value' attribute.")

    return net_path

def write_gpickle(graph: nx.Graph, filepath: str):
    """
    Salva um grafo NetworkX em formato binário (.gpickle) usando pickle.
    """
    with open(filepath, "wb") as f:
        pickle.dump(graph, f)
    print(f"Grafo salvo com sucesso em '{filepath}'.")

def read_gpickle(filepath: str, debugging: bool = False) -> nx.Graph:
    """
    Carrega um grafo NetworkX salvo anteriormente com pickle.
    """
    with open(filepath, "rb") as f:
        graph = pickle.load(f)

    if debugging: print(f"Grafo carregado com sucesso de '{filepath}'.")

    return graph

def get_simulation_bounds(SUMOCFG_FILE):

    slash_index = SUMOCFG_FILE.rfind('/') + 1 # finds '/' from right to left
    sumocfg_dir = SUMOCFG_FILE[:slash_index] # return a substring from 0 to slash_index
    net_file_path = sumocfg_dir + extract_net_path(SUMOCFG_FILE)

    # Extrai os limites espaciais da simulação (bounding box) do arquivo .net.xml.
    # Retorna como um dicionário com xmin, ymin, xmax, ymax.

    tree = ET.parse(net_file_path)
    root = tree.getroot()

    location = root.find("location")

    if location is not None and "convBoundary" in location.attrib:

        xmin, ymin, xmax, ymax = map(float, location.attrib["convBoundary"].split(','))

        return {
            "xmin": xmin,
            "ymin": ymin,
            "xmax": xmax,
            "ymax": ymax
        }

    else:
        raise ValueError("Não foi possível encontrar a boundary no arquivo .net.xml.")

def debug_stats(G, step, metrics):

    n = len(metrics["articulation_points"])

    print(f"Number of edges: {G.number_of_edges()}")
    print(f"Number of nodes: {G.number_of_nodes()}")
    print(f"Graph Density: {nx.density(G) * 100:.2f}%")
    print(f"[time={step // 60 ** 2}h:{step // 60}m:{step}s] {n} articulation points")

    # if n > 15:
    #     print(metrics["articulation_points"])
    #     nx.draw(G, with_labels = True)  # Desenha com rótulos nos nós
    #     plt.show()

    print("-----------------------------")
