# map_name="santa_tereza"
# map_name="bh_contorno"
map_name="sao_paulo"

mkdir -p ../net

netconvert \
	--osm-files ../maps/${map_name}.osm \
	--output-file ../net/${map_name}.net.xml

mkdir -p ../routes

# --trip-attributes="departLane=\"best\" departSpeed=\"max\" departPos=\"random\"" \
# -b 0 \ # Begin time (e.g., 0 seconds)
# -e 1000 \ # End time (e.g., 1000 seconds)
# -p 2 \ # Trip generation interval (a new trip every 2 seconds on average)
python3 /usr/share/sumo/tools/randomTrips.py \
	-n ../net/${map_name}.net.xml \
	-o ../routes/${map_name}.trips.xml \
	-r ../routes/${map_name}.rou.xml \
	--begin 0 --end 1000 --period 1 --binomial 10 \
	--validate
