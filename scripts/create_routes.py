# Dictionary-based definition of traffic periods
traffic_periods = {

    "night_cars": {
        "begin": 0,
        "end": 21600,
        "period": 5,
        "vtype": "car",
        "label": "00:00–06:00 (cars)",
        "color": "#f0f0f0"
    },

    "morning_rush_cars":  {
        "begin": 21600,
        "end": 36000,
        "period": 2,
        "vtype": "car",
        "label": "06:00–10:00 (cars)",
        "color": "#ffdede"
    },

    "morning_rush_buses": {
        "begin": 21600,
        "end": 36000,
        "period": 20,
        "vtype": "bus",
        "label": "06:00–10:00 (buses)",
        "color": "#ffdede"
    },

    "midday_cars": {
        "begin": 36000,
        "end": 57600,
        "period": 4,
        "vtype": "car",
        "label": "10:00–16:00 (cars)",
        "color": "#e0f7ff"
    },

    "midday_taxis": {
        "begin": 36000,
        "end": 57600,
        "period": 2,
        "vtype": "taxi",
        "label": "10:00–16:00 (taxis)",
        "color": "#e0f7ff"
    },

    "midday_buses": {
        "begin": 36000,
        "end": 57600,
        "period": 30,
        "vtype": "bus",
        "label": "10:00–16:00 (buses)",
        "color": "#e0f7ff"
    },

    "evening_rush_cars": {
        "begin": 57600,
        "end": 72000,
        "period": 2,
        "vtype": "car",
        "label": "16:00–20:00 (cars)",
        "color": "#ffdede"
    },

    "evening_rush_buses": {
        "begin": 57600,
        "end": 72000,
        "period": 20,
        "vtype": "bus",
        "label": "16:00–20:00 (buses)",
        "color": "#ffdede"
    },

    "late_evening_cars": {
        "begin": 72000,
        "end": 86400,
        "period": 5,
        "vtype": "car",
        "label": "20:00–24:00 (cars)",
        "color": "#f0f0f0"
    },
}

def prepare_route():

    # Prepare script lines from dictionary
    lines = []

    for i, (_, info) in enumerate(traffic_periods.items()):

        trip_file = f"routes/{TRACE_NAME}_{info['vtype']}_{i}.trips.xml"
        route_file = f"routes/{TRACE_NAME}_{info['vtype']}_{i}.rou.xml"
        lines.append(f"# {info['label']}")
        lines.append(
            f"python3 /usr/share/sumo/tools/randomTrips.py "
            f"-n {NET_FILE} "
            f"-o {trip_file} "
            f"-r {route_file} "
            f"--begin {info['begin']} --end {info['end']} "
            f"--period {info['period']} "
            f"--vtype {info['vtype']} "
            f"--prefix {info['vtype']}_{i}_ "
            f"--validate"
        )

    bash_script = "\n\n".join(lines)

    # Define the script path
    script_path = "bash/generate_routes.sh"

    # Write to file
    with open(script_path, "w") as f:
        f.write("#!/bin/bash\n\n")
        f.write(bash_script + "\n")

    # Make the script executable
    os.chmod(script_path, 0o755)

    # Optional: execute the script
    subprocess.run(["bash", script_path], check=True)

    print(f"Route generation script written and executed: {script_path}")

def merge_routes(output_path=f"routes/{TRACE_NAME}.rou.xml"):

    root = ET.Element("routes")
    vtype_set = set()  # Para evitar duplicatas de <vType>

    for i, (_, info) in enumerate(traffic_periods.items()):
        route_path = f"routes/{TRACE_NAME}_{info['vtype']}_{i}.rou.xml"
        if not os.path.exists(route_path):
            print(f"Arquivo não encontrado: {route_path}")
            continue

        tree = ET.parse(route_path)
        sub_root = tree.getroot()

        for elem in sub_root:
            if elem.tag == "vType":
                # Evitar duplicatas de vType com mesmo ID
                vtype_id = elem.attrib.get("id")
                if vtype_id in vtype_set:
                    continue
                vtype_set.add(vtype_id)

            root.append(elem)

    # Escrevendo o novo arquivo
    tree = ET.ElementTree(root)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    tree.write(output_path, encoding="UTF-8", xml_declaration=True)
    print(f"Rotas mescladas salvas em: {output_path}")

if __name__ == "__main__":
    # prepare_route()
    # merge_routes()
