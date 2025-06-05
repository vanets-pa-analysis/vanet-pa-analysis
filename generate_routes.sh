#!/bin/bash

# 00:00–06:00 (cars)

python3 /usr/share/sumo/tools/randomTrips.py -n net/sao_paulo.net.xml -o routes/sao_paulo_car_0.trips.xml -r routes/sao_paulo_car_0.rou.xml --begin 0 --end 21600 --period 5 --vtype car --validate

# 06:00–10:00 (cars)

python3 /usr/share/sumo/tools/randomTrips.py -n net/sao_paulo.net.xml -o routes/sao_paulo_car_1.trips.xml -r routes/sao_paulo_car_1.rou.xml --begin 21600 --end 36000 --period 0.5 --vtype car --validate

# 06:00–10:00 (buses)

python3 /usr/share/sumo/tools/randomTrips.py -n net/sao_paulo.net.xml -o routes/sao_paulo_bus_2.trips.xml -r routes/sao_paulo_bus_2.rou.xml --begin 21600 --end 36000 --period 20 --vtype bus --validate

# 10:00–16:00 (cars)

python3 /usr/share/sumo/tools/randomTrips.py -n net/sao_paulo.net.xml -o routes/sao_paulo_car_3.trips.xml -r routes/sao_paulo_car_3.rou.xml --begin 36000 --end 57600 --period 4 --vtype car --validate

# 10:00–16:00 (taxis)

python3 /usr/share/sumo/tools/randomTrips.py -n net/sao_paulo.net.xml -o routes/sao_paulo_taxi_4.trips.xml -r routes/sao_paulo_taxi_4.rou.xml --begin 36000 --end 57600 --period 2 --vtype taxi --validate

# 10:00–16:00 (buses)

python3 /usr/share/sumo/tools/randomTrips.py -n net/sao_paulo.net.xml -o routes/sao_paulo_bus_5.trips.xml -r routes/sao_paulo_bus_5.rou.xml --begin 36000 --end 57600 --period 30 --vtype bus --validate

# 16:00–20:00 (cars)

python3 /usr/share/sumo/tools/randomTrips.py -n net/sao_paulo.net.xml -o routes/sao_paulo_car_6.trips.xml -r routes/sao_paulo_car_6.rou.xml --begin 57600 --end 72000 --period 0.5 --vtype car --validate

# 16:00–20:00 (buses)

python3 /usr/share/sumo/tools/randomTrips.py -n net/sao_paulo.net.xml -o routes/sao_paulo_bus_7.trips.xml -r routes/sao_paulo_bus_7.rou.xml --begin 57600 --end 72000 --period 20 --vtype bus --validate

# 20:00–24:00 (cars)

python3 /usr/share/sumo/tools/randomTrips.py -n net/sao_paulo.net.xml -o routes/sao_paulo_car_8.trips.xml -r routes/sao_paulo_car_8.rou.xml --begin 72000 --end 86400 --period 5 --vtype car --validate
