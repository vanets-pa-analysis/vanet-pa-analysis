import os
import traci
from traci import simulation as sim

import scripts.utils as utils
import scripts.visualization as vis

from scripts.build_graph import build_graph
from scripts.metrics import calcular_metricas

TRACES_PATH = {
    "santa_tereza": "santa_tereza/santa_tereza",
    "sao_paulo"   : "sao_paulo/sao_paulo",
    "luxemburg"   : "LuSTScenario/scenario/due.actuated",
    "monaco"      : "MoSTScenario/scenario/most",
}

TRACE_NAME              = "monaco"
SUMOCFG_FILE            = f"traces/{TRACES_PATH[TRACE_NAME]}.sumocfg"
BOUNDS                  = utils.get_simulation_bounds(SUMOCFG_FILE)
END_TIME                = utils.get_end_time(SUMOCFG_FILE)
SUMO_CONFIG             = "sumo-gui"

METRICS_EVERY_N_SECONDS = 60
DISTANCE_THRESHOLD      = 100
DEBUGGING               = False
SAVE_RESULTS            = False
GET_METRICS             = True

def main():

    traci.start([SUMO_CONFIG, "-c", SUMOCFG_FILE])

    step, csv_data, geoPosAPs = 0, [], []

    while step <= END_TIME and sim.getMinExpectedNumber() > 0:

        traci.simulationStep()
        step = sim.getTime()

        if step % METRICS_EVERY_N_SECONDS != 0: continue

        if GET_METRICS:
            positions = utils.get_vehicle_positions()
            G = build_graph(positions, DISTANCE_THRESHOLD, use_quadTree = (True, BOUNDS))

            # Salvar estatísticas
            metrics, coordenates = calcular_metricas(G, positions, multithreaded = False)
            geoPosAPs.append(coordenates)
            csv_data.append([metrics[m] for m in metrics])

            if DEBUGGING: utils.debug_stats(G, step, metrics)

    traci.close()

    if SAVE_RESULTS:
        outputPath = f"output/simulation_{utils.getNextSimID()}_{TRACE_NAME}_{step - 1}s_{DISTANCE_THRESHOLD}m/"
        os.makedirs(outputPath, exist_ok = True)

        vis.generate_histograms(csv_data, outputPath)
        vis.generate_heat_map(geoPosAPs, outputPath)

if __name__ == "__main__": main()
