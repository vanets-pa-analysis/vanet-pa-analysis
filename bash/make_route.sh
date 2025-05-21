mkdir -p ../routes
python3 /usr/share/sumo/tools/randomTrips.py \
	-n ../net/santa_tereza.net.xml \
	-o ../routes/santa_tereza.trips.xml \
	-r ../routes/santa_tereza.rou.xml \
	--begin 0 --end 1000 --period 1 --binomial 10 \
	--validate
