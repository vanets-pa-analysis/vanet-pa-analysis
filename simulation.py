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

TRACE_NAME              = "luxemburg"
SUMOCFG_FILE            = f"traces/{TRACES_PATH[TRACE_NAME]}.sumocfg"
BOUNDS                  = utils.get_simulation_bounds(SUMOCFG_FILE)
END_TIME                = utils.get_end_time(SUMOCFG_FILE)
SUMO_CONFIG             = "sumo-gui"

METRICS_EVERY_N_SECONDS = 60
DISTANCE_THRESHOLD      = 100
DEBUGGING               = False
SAVE_RESULTS            = True
GET_METRICS             = True

VEICULOS = {
    "bus": "AVL",
    "car": "car",
}

def main():

    step, csv_data, geoPosAPs = run_simulation()

    if SAVE_RESULTS:
        save_results(csv_data, geoPosAPs, step)

def run_simulation():

    traci.start([SUMO_CONFIG, "-c", SUMOCFG_FILE])
    step, csv_data, geoPosAPs = 0, [[]] * (len(VEICULOS) + 1), []

    while step <= END_TIME and sim.getMinExpectedNumber() > 0:

        traci.simulationStep()
        step = sim.getTime()

        if GET_METRICS and step % METRICS_EVERY_N_SECONDS == 0:
            step_metrics(step, csv_data, geoPosAPs)

    traci.close()

    return step, csv_data, geoPosAPs

def step_metrics(step, csv_data, geoPosAPs):

    positions = utils.get_vehicle_positions()
    print(f"positions: {positions}")
    G = build_graph(positions, DISTANCE_THRESHOLD, use_quadTree = (True, BOUNDS))
    print(f"G: {G}")

    # Salvar estatísticas
    metrics_list, coordenates = calcular_metricas(VEICULOS, G, positions, multithreaded = False)
    geoPosAPs.append(coordenates)

    print(f"metrics_list: {metrics_list}")
    print(f"geoPosAPs: {geoPosAPs}")

    for i in range(len(metrics_list)):
        csv_data[i].append([m for m in metrics_list[i].values() if type(m) != list])

    if DEBUGGING:
        for metrics in metrics_list:
            utils.debug_stats(G, step, metrics)

def save_results(csv_data, geoPosAPs, step):

    outputPath = f"output/simulation_{utils.getNextSimID()}_{TRACE_NAME}_{(step - 1):.0f}s_{DISTANCE_THRESHOLD}m/"
    os.makedirs(outputPath, exist_ok = True)

    vis.generate_histograms(csv_data[0], outputPath)
    vis.generate_heat_map(geoPosAPs, outputPath)

    index = 1
    for key in VEICULOS:

        outputPathVeiculo = outputPath + key + "/"
        os.makedirs(outputPathVeiculo, exist_ok = True)

        vis.generate_histograms(csv_data[index], outputPathVeiculo)
        index += 1

if __name__ == "__main__": main()
