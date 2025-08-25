import os
import traci
from traci import simulation as sim

from tqdm import tqdm as progress_bar

import networkx as nx

from scripts.build_graph import build_graph, update_vehicle_positions
import scripts.utils as utils
from scripts.utils import Timer

from scripts.utils import ap_geographical_position

###################################################

TRACE_NAME                  = "monaco"
USE_GUI                     = False
METRICS_EVERY_N_SIM_SECONDS = 60
DISTANCE_THRESHOLD          = 100
DEBUGGING                   = False
SIMULATION_WARNINGS         = False
USING_QUAD_TREE             = True

###################################################

TRACES_PATH = {
    "santa_tereza": "santa_tereza/santa_tereza",
    "sao_paulo"   : "sao_paulo/sao_paulo",
    "luxembourg"   : "LuSTScenario/scenario/due.actuated",
    "monaco"      : "MoSTScenario/scenario/most",
}

SUMOCFG_FILE      = f"traces/{TRACES_PATH[TRACE_NAME]}.sumocfg"
BOUNDS            = utils.get_simulation_bounds(SUMOCFG_FILE)
END_TIME          = utils.get_end_time(SUMOCFG_FILE)
BEGIN_TIME        = utils.get_begin_time(SUMOCFG_FILE) 
# END_TIME        = 3600
SIM_WARNINGS_FLAG = [] if SIMULATION_WARNINGS else ["--no-warnings", "--no-step-log"]
SUMO_CONFIG       = "sumo-gui" if USE_GUI else "sumo"

def update_prog_bar(prog_bar: progress_bar, graph_build_timer: Timer, positions_update_timer: Timer, graph_save_timer: Timer, subscribed_vehicles: set):

    # Get timings
    pos_time = positions_update_timer.time()
    build_time = graph_build_timer.time()
    total_main_time = pos_time + build_time

    if total_main_time > 0:
        pos_pct = (pos_time / total_main_time) * 100
        build_pct = 100 - pos_pct
    else:
        pos_pct = build_pct = 0

    prog_bar.set_postfix({
        "cars": len(subscribed_vehicles),
        "building": f"{total_main_time:.3f}s",
        "saving": f"{graph_save_timer.time():.3f}s",
        "time % building/updating": f"{build_pct:.0f}/{pos_pct:.0f}"
    })

def main():

    traci.start([SUMO_CONFIG, "-c", SUMOCFG_FILE] + SIM_WARNINGS_FLAG)

    prog_bar = progress_bar(total=END_TIME, desc="Simulating", unit="step")

    step = BEGIN_TIME

    output_path = f"saved_graphs/simulation_{utils.getNextSimID("saved_graphs")}_{TRACE_NAME}_{(END_TIME):.0f}s_{DISTANCE_THRESHOLD}m/"
    os.makedirs(output_path, exist_ok = True)

    prog_bar = progress_bar(total=END_TIME, desc=f"Simulating {"using QT" if USING_QUAD_TREE else "not using QT"}", unit="step")
    subscribed_vehicles = set()
    graph_build_timer, positions_update_timer, graph_save_timer = Timer(), Timer(), Timer()

    step = 0
    traci.start([SUMO_CONFIG, "-c", SUMOCFG_FILE] + SIM_WARNINGS_FLAG)

    while step <= END_TIME and sim.getMinExpectedNumber() > 0:

        traci.simulationStep()
        prog_bar.update(sim.getTime() - step)

        step = sim.getTime()

        if step % METRICS_EVERY_N_SIM_SECONDS == 0:

            positions_update_timer.start()
            positions = update_vehicle_positions(subscribed_vehicles)
            lat_lon = {key: ap_geographical_position(value) for key, value in positions.items()}
            positions_update_timer.end()

            graph_build_timer.start()
            G: nx.Graph = build_graph(positions, lat_lon, DISTANCE_THRESHOLD, use_quadTree = (True, BOUNDS))
            graph_build_timer.end()

            graph_save_timer.start()
            nx.write_gpickle(G, f"{output_path}/graph_{step}.gpickle")
            graph_save_timer.end()

            update_prog_bar(prog_bar, graph_build_timer, positions_update_timer, graph_save_timer, subscribed_vehicles)

            if DEBUGGING:
                print(f"Number of nodes: {G.number_of_nodes()}")
                print(f"Number of AP: {len(list(nx.articulation_points(G)))}")
                print(f"Number of edges: {G.number_of_edges()}")

                #NOTE: X & Y
                # if len(positions) > 0:
                first_key = list(positions.keys())[0]
                print(" pos:", positions[first_key])

                #TODO: TIRAR DPS
                #NOTE: lat lon
                second_key = list(lat_lon.keys())[0]
                print("new pos:", lat_lon[second_key])

    prog_bar.close()
    traci.close()

if __name__ == "__main__": main()
