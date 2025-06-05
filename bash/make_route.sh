mkdir -p ../routes

<<<<<<< Updated upstream
# pico manhã (7h–9h) → carros e ônibus
python3 /usr/share/sumo/tools/randomTrips.py -n ../net/santa_tereza.net.xml -o ../routes/pico_manha_car.trips.xml -r ../routes/pico_manha_car.rou.xml --begin 25200 --end 32400 --period 1 --binomial 30 --vtype car --prefix car

python3 /usr/share/sumo/tools/randomTrips.py -n ../net/santa_tereza.net.xml -o ../routes/pico_manha_bus.trips.xml -r ../routes/pico_manha_bus.rou.xml --begin 25200 --end 32400 --period 30 --binomial 2 --vtype bus --prefix bus

# pico noite (17h–19h)
python3 /usr/share/sumo/tools/randomTrips.py -n ../net/santa_tereza.net.xml -o ../routes/pico_noite_car.trips.xml -r ../routes/pico_noite_car.rou.xml --begin 61200 --end 68400 --period 1 --binomial 30 --vtype car --prefix car

python3 /usr/share/sumo/tools/randomTrips.py -n ../net/santa_tereza.net.xml -o ../routes/pico_noite_bus.trips.xml -r ../routes/pico_noite_bus.rou.xml --begin 61200 --end 68400 --period 30 --binomial 2 --vtype bus --prefix bus

# madrugada (00h–6h)
python3 /usr/share/sumo/tools/randomTrips.py -n ../net/santa_tereza.net.xml -o ../routes/madrugada_car.trips.xml -r ../routes/madrugada_car.rou.xml --begin 0 --end 21600 --period 1 --binomial 5 --vtype car --prefix car

# dia inteiro → táxis
python3 /usr/share/sumo/tools/randomTrips.py -n ../net/santa_tereza.net.xml -o ../routes/dia_taxi.trips.xml -r ../routes/dia_taxi.rou.xml --begin 0 --end 86400 --period 5 --binomial 5 --vtype taxi --prefix taxi

=======
# --trip-attributes="departLane=\"best\" departSpeed=\"max\" departPos=\"random\"" \
# -b 0 \ # Begin time (e.g., 0 seconds)
# -e 1000 \ # End time (e.g., 1000 seconds)
# -p 2 \ # Trip generation interval (a new trip every 2 seconds on average)
python3 /usr/share/sumo/tools/randomTrips.py \
	-n ../net/${map_name}.net.xml \
	-o ../routes/${map_name}.trips.xml \
	-r ../routes/${map_name}.rou.xml \
	--begin 0 --end 86400 --period 5 --binomial 1 \
	--validate
>>>>>>> Stashed changes
