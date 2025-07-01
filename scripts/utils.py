import traci
import networkx as nx
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

def get_vehicle_positions():

    positions = {}

    for vid in traci.vehicle.getIDList():
        x, y = traci.vehicle.getPosition(vid)
        positions[vid] = (x, y)

    return positions

def getNextSimID():

    path = "output/lastSimulationID.txt"

    # Read the current ID
    with open(path, "r") as f:
        lastSimID = int(f.read())

    # Increment the ID
    lastSimID += 1

    # Overwrite with the new ID
    with open(path, "w") as f:
        f.write(str(lastSimID))

    return lastSimID

def get_end_time(sumocfg_path):

    tree = ET.parse(sumocfg_path)
    root = tree.getroot()

    for time_tag in root.findall("time"):

        end = time_tag.find("end")

        if end is not None:
            return float(end.attrib["value"])

    return None

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

def get_simulation_bounds(SUMOCFG_FILE):

    slash_index = SUMOCFG_FILE.rfind('/') + 1 # finds '/' from right to left
    sumocfg_dir = SUMOCFG_FILE[:-slash_index] # return a substring from 0 to len -slash_index
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
