# About
Bla bla, content and short description


# Yr
Create the container that retrieves data from [yr.no](https://www.yr.no) with the command below. This container only retrieves data from [yr.no](https://www.yr.no) and sends it to the mqtt broker. It does not need to persist data. The commands must be run from the directory that contains `Dockerfile` and `requirements.txt` . Update the `urls.json` file Yr resources as required.

`docker build -t yr .`

```
docker run -d \`  
--name=yr \`  
-e TZ=Europe/Stockholm \`  
--restart unless-stopped \` 
yr \`  
./send_yr.py \`  
--debug no \`  
--url_file <path and filename of json file with Yr resources>`
--user_agent <email address of entity using the API> \`  
--mqtt_host <mosquitto host> \`  
--mqtt_port 1883 \`  
--mqtt_topic <mosquitto topic> \`  
--mqtt_client_id <mosquitto clientID>`
```
