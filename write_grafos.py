import os
import traci
from traci import simulation as sim

from tqdm import tqdm as progress_bar

import networkx as nx
from networkx.readwrite.gpickle import write_gpickle

from scripts.build_graph import build_graph, update_vehicle_positions
import scripts.utils as utils

###################################################

TRACE_NAME                  = "luxembourg"
USE_GUI                     = False
METRICS_EVERY_N_SIM_SECONDS = 60
DISTANCE_THRESHOLD          = 100
DEBUGGING                   = False
SIMULATION_WARNINGS         = False

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
SIM_WARNINGS_FLAG = [] if SIMULATION_WARNINGS else ["--no-warnings", "--no-step-log"]
SUMO_CONFIG       = "sumo-gui" if USE_GUI else "sumo"

def main():

    traci.start([SUMO_CONFIG, "-c", SUMOCFG_FILE] + SIM_WARNINGS_FLAG)

    prog_bar = progress_bar(total=END_TIME, desc="Simulating", unit="step")

    step = 0

    output_path = f"saved_graphs/simulation_{utils.getNextSimID("saved_graphs")}_{TRACE_NAME}_{(END_TIME):.0f}s_{DISTANCE_THRESHOLD}m/"
    os.makedirs(output_path, exist_ok = True)

    subscribed_vehicles = set()

    while step <= END_TIME and sim.getMinExpectedNumber() > 0:

        traci.simulationStep()
        prog_bar.update(sim.getTime() - step)

        step = sim.getTime()

        if step % METRICS_EVERY_N_SIM_SECONDS == 0:

            positions = update_vehicle_positions(subscribed_vehicles)
            G: nx.Graph = build_graph(positions, DISTANCE_THRESHOLD, use_quadTree = (True, BOUNDS))

            write_gpickle(G, f"{output_path}/graph_{step}.gpickle")

    prog_bar.close()
    traci.close()

if __name__ == "__main__": main()
