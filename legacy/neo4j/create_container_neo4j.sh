#!/bin/bash

set -o xtrace

# Create the container
docker run -d \
  --name=neo4j \
  -e TZ=Europe/Stockholm \
  --volume /home/pi/neo4j:/data \
  --restart unless-stopped \
  --publish=7474:7474 --publish=7687:7687 \
  -e NEO4J_server_default__listen__address=0.0.0.0 \
neo4j


# Refer to https://neo4j.com/docs/operations-manual/current/docker/ref-settings/