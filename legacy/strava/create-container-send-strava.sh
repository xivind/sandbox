#!/bin/bash

# Build the image and tag it
docker build -t strava -f send-strava.Dockerfile .

# Create the container
docker run -d \
  --name=strava \
  -e TZ=Europe/Stockholm \
  -v /home/user/secrets:/secrets \
  --restart unless-stopped \
  strava \
  ./send_strava.py \
  --oauth_file /secrets/strava_tokens.json \
  --mqtt_host mqtt_broker \
  --mqtt_port 1883 \
  --mqtt_topic strava \
  --mqtt_client_id send_strava