#!/bin/bash

# map_name="santa_tereza"
# map_name="bh_contorno"
# map_name="redondezas_puc"
map_name="sao_paulo"

mkdir -p ../net

# This line uses netconvert, a tool provided by SUMO,
# to convert the .osm map into a SUMO network file (.net.xml),
# which can be used for simulations.
netconvert \
	--osm-files ../maps/${map_name}.osm \
	--output-file ../net/${map_name}.net.xml \
