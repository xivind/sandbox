# Background
The code in this repo is meant for experimenting and learning basic programming, with emphasis on containers, messagebrokers, data visualisation and git as a bonus. Some of the sources that are used are [strava.com](https://www.strava.com), [yr.no](https://www.yr.no) and [nilu.no](https://www.nilu.no). InfluxDB is used to store the data, Grafana to visualize the data and Mosquitto to move data across the containers. The scripts that interacts with the data sources are all python. Everything runs in docker containers. The code is tested on Raspberry Pi 4b.

- **The code is for testing purposes only, so security is not configured**
- **All comments, suggestions and pull requests to improve the code is very welcome, see open issues..**
- **This is a learning effort, so expect many strange choices and errors in the code, waiting to be corrected**

# InfluxDB
Create the InfluxDB container with the command below. This is the container that runst the actualt InfluxDB server. To persist the data create a docker volume first. And also update the path to the default InfluxDB config file, influxdb.conf.
> `docker run -d \`  
`--name=influxdb \`  
`-e TZ=Europe/Stockholm \`  
`--mount type=bind,source=/<path on host>/influxdb.conf,target=/etc/influxdb/influxdb.conf \`  
`--mount type=volume,source=<docker volume on host>,target=/var/lib/influxdb \`  
`-p 8086:8086 \`  
`--restart unless-stopped \`  
`influxdb:1.8.6 -config /etc/influxdb/influxdb.conf`

With the commands below, build the image and create the container that will run the python script that writes to InfluxDB. The python script listens to mqtt for messages with data to write. See the Strava container below for an example of how the messages must be formatted. Create a separeate container for each data source, e.g. one for Strava, one for Yr etc. The commands must be run from the directory that contains `Dockerfile` and `requirements.txt` 
> `docker build -t <name of image> .`

> `docker run -d \`  
`--name=<name of container> \`  
`-e TZ=Europe/Stockholm \`  
`--restart unless-stopped \`  
`<name of image> \`  
`./receive-timeseries.py \`  
`--mqttHost <mosquitto host> \`  
`--mqttPort 1883 \`  
`--mqttKeepalive 60 \`  
`--mqttTopic <mosquitto topic> \`  
`--influxHost <influxdb host> \`  
`--influxPort 8086 \`  
`--influxUser <influxdb user> \`  
`--influxPassword <influxdb password> \`  
`--influxDatabase <influxdb database> \`  
`--influxMeasurement <influxdb measurement>`
# Strava
Create the container that retrieves data from Strava with the command below. This container only retrieves data from Strava and sends it to the mqtt broker. It does not need to persist data. The commands must be run from the directory that contains `Dockerfile` and `requirements.txt`
> `docker build -t strava .`

> `docker run -d \`  
`--name=strava \`  
`-e TZ=Europe/Stockholm \`  
`-v /<path on host to directory containing file with tokens>:/secrets \`  
`--restart unless-stopped \`  
`strava \`  
`./send-strava.py \`  
`--debug no \`  
`--tokens /secrets/<name of filen with tokens> \`  
`--mqttHost <mosquitto host> \`  
`--mqttPort 1883 \`  
`--mqttTopic <mosquitto topic> \`  
`--mqttClientID <mosquitto clientID>`

Strava requires authentication with OAuth2. It looks complicated, but is fairly straight forward to configure if you follow [Stravas step-by-step guide](https://developers.strava.com/docs/getting-started/#oauth). In the script we are using here, the tokens are handled through a json file, which must look as following. [Thanks to Pauls Geek Dad Blog](https://pdwhomeautomation.blogspot.com/2016/01/fitbit-api-access-using-oauth20-and.html) for pointing us in the right direction with python and OAuth2 also.
>`{"clientId": "", "clientSecret": "", "accessToken": "", "refreshToken": ""}`


# Fitbit
Coming soon...

# Nilu

# Yr

# Grafana
See grafana shares, pictures
# Blinkt
