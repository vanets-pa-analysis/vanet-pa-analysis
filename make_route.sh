mkdir -p routes
python3 /usr/share/sumo/tools/randomTrips.py \
  -n net/bh.net.xml \
  -o routes/bh.trips.xml \
  -r routes/bh.rou.xml \
  --begin 0 --end 3600 --period 0.005 \
  --validate
