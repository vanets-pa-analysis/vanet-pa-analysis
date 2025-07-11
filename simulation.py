import traci
from traci import simulation as sim

import scripts.utils as utils
from teste import ConcreteClass1

###################################################

TRACE_NAME              = "santa_tereza"
# TRACE_TYPE              = Extractors.Extractor1
SUMO_CONFIG             = "sumo-gui"
METRICS_EVERY_N_SECONDS = 60
DISTANCE_THRESHOLD      = 100
DEBUGGING               = False
SAVE_RESULTS            = True
CALCULATE_METRICS       = True

###################################################

TRACES_PATH = {
    "santa_tereza": "santa_tereza/santa_tereza",
    "sao_paulo"   : "sao_paulo/sao_paulo",
    "luxemburg"   : "LuSTScenario/scenario/due.actuated",
    "monaco"      : "MoSTScenario/scenario/most",
}

SUMOCFG_FILE = f"traces/{TRACES_PATH[TRACE_NAME]}.sumocfg"
BOUNDS       = utils.get_simulation_bounds(SUMOCFG_FILE)
END_TIME     = utils.get_end_time(SUMOCFG_FILE)

def main():

    traci.start([SUMO_CONFIG, "-c", SUMOCFG_FILE])

    metrics_extractor = ConcreteClass1(
        distance_threshold = DISTANCE_THRESHOLD,
        metrics_every_n_seconds = METRICS_EVERY_N_SECONDS,
        use_quad_tree = (True, BOUNDS)
        # multithreaded = False
    )

    step = 0

    while step <= END_TIME and sim.getMinExpectedNumber() > 0:

        traci.simulationStep()
        step = sim.getTime()

        if CALCULATE_METRICS:
            metrics_extractor.extract_data(step)

    traci.close()

    if SAVE_RESULTS:
        metrics_extractor.save_data()

if __name__ == "__main__": main()
