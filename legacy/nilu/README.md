# About
Bla bla, content and short description


# Nilu
Create the container that retrieves data from [nilu.no](https://www.nilu.no) with the command below. This container only retrieves data from [nilu.no](https://www.nilu.no) and sends it to the mqtt broker. It does not need to persist data. The commands must be run from the directory that contains `Dockerfile` and `requirements.txt`

`docker build -t nilu .`

```
docker run -d \  
--name=nilu \  
-e TZ=Europe/Stockholm \  
--restart unless-stopped \ 
nilu \  
./send_nilu.py \  
--debug no \  
--url <URl to Nilus API>
--user_agent <email address of entity using the API> \  
--mqtt_host <mosquitto host> \  
--mqtt_port 1883 \  
--mqtt_topic <mosquitto topic> \  
--mqtt_client_id <mosquitto clientID>
```

