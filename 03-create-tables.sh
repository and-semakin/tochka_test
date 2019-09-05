#!/bin/bash
command -v docker-compose >/dev/null 2>&1 || { echo >&2 "This script requires `docker-compose` but it's not installed.  Aborting."; exit 1; }
QUERIES=./sql/*.sql
for q in $QUERIES
do
  echo "Processing $q..."
  docker-compose exec -T postgres psql -U bank < $q
  echo "====================="
done
echo "Done."
