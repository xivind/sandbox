#!/bin/bash

# Build the image and tag it
docker build -t finance -f send-finance.Dockerfile .

# Create the container
docker run -d \
  --name=finance \
  -e TZ=Europe/Stockholm \
  -v <HOST DIRECTORY WITH OAUTH_FILE>:/secrets \
  --restart unless-stopped \
  finance \
  ./send_transactions.py \
  --oauth_file /secrets/sbanken_oauth.json \
  --card_provider sbanken \
  --mqtt_host <MQTT HOSTNAME> \
  --mqtt_port <MQTT PORT> \
  --mqtt_topic <MQTT TOPIC> \
  --mqtt_client_id <MQTT CLIENT ID>