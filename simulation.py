import traci
from traci import simulation as sim

from tqdm import tqdm as progress_bar

import scripts.utils as utils
from teste import extractor_factory

###################################################

TRACE_NAME                  = "luxembourg"
USE_GUI                     = False # "sumo-gui" / "sumo"
METRICS_EVERY_N_SIM_SECONDS = 60
DISTANCE_THRESHOLD          = 100
DEBUGGING                   = False
SIMULATION_WARNINGS         = False
CALCULATE_METRICS           = True
SAVE_RESULTS                = False

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

    metrics_extractor = extractor_factory(
        TRACE_NAME,
        distance_threshold = DISTANCE_THRESHOLD,
        metrics_every_n_seconds = METRICS_EVERY_N_SIM_SECONDS,
        use_quad_tree = (True, BOUNDS),
        debugging = DEBUGGING,
        progress_bar = prog_bar
        # multithreaded = False
    )

    step = 0

    while step <= END_TIME and sim.getMinExpectedNumber() > 0:

        traci.simulationStep()
        prog_bar.update(sim.getTime() - step)

        step = sim.getTime()

        if CALCULATE_METRICS:
            metrics_extractor.extract_data(step)
        else:
            prog_bar.set_postfix({"cars": len(traci.vehicle.getIDList())})

    prog_bar.close()
    traci.close()

    if CALCULATE_METRICS and SAVE_RESULTS:
        outputPath = f"output/simulation_{utils.getNextSimID()}_{TRACE_NAME}_{(step - 1):.0f}s_{DISTANCE_THRESHOLD}m/"
        metrics_extractor.save_data(outputPath)

if __name__ == "__main__": main()
