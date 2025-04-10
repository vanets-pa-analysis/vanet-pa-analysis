osmfilter bh.osm \
  --keep="highway=" \
  --ignore-dependencies \
  --drop-author \
  --drop-version \
  > bh_filtered.osm
