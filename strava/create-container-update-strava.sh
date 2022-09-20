#!/bin/bash

# Build the image and tag it
docker build -t update-strava -f update-strava.Dockerfile .

# Create the container
docker run -d \
  --name=update-strava \
  -e TZ=Europe/Stockholm \
  -v /home/pi/code/secrets:/secrets \
  --restart unless-stopped \
  update-strava \
  ./update_strava.py \
  --oauth_file /secrets/strava_tokens.json \
  --gear_file /secrets/strava_gear.json