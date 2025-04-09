#!/bin/bash

mkdir -p net

netconvert \
  --osm-files bh_filtered.osm \
  --output-file net/bh.net.xml
