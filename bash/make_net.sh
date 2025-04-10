#!/bin/bash

mkdir -p ../net

netconvert \
  --osm-files ../maps/santa_tereza.osm \
  --output-file ../net/santa_tereza.net.xml
