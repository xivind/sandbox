# About
Bla bla, content and short description

influx -database datastore -execute "SELECT * FROM climate WHERE "serial" = '100000003b5573e2''" -format csv > test2.csv

NO LONGER IN USE
Create the InfluxDB container with the command below. This is the container that runst the actualt InfluxDB server. To persist the data create a docker volume first. And also update the path to the default InfluxDB config file, `influxdb.conf`.
```
docker run -d \  
--name=influxdb \  
-e TZ=Europe/Stockholm \  
--mount type=bind,source=/<path on host>/influxdb.conf,target=/etc/influxdb/influxdb.conf \  
--mount type=volume,source=<docker volume on host>,target=/var/lib/influxdb \  
-p 8086:8086 \  
--restart unless-stopped \  
influxdb:1.8.6 -config /etc/influxdb/influxdb.conf
```
With the commands below, build the image and create the container that will run the python script that writes to InfluxDB. The python script listens to mqtt for messages with data to write. See the Strava container below for an example of how the messages must be formatted. Create a separeate container for each data source, e.g. one for Strava, one for Yr etc. The commands must be run from the directory that contains `Dockerfile` and `requirements.txt`  

`docker build -t <name of image> .`

```
docker run -d \  
--name=<name of container> \  
-e TZ=Europe/Stockholm \  
--restart unless-stopped \  
<name of image> \  
./receive-timeseries.py \  
--mqttHost <mosquitto host> \  
--mqttPort 1883 \  
--mqttKeepalive 60 \  
--mqttTopic <mosquitto topic> \  
--influxHost <influxdb host> \  
--influxPort 8086 \  
--influxUser <influxdb user> \  
--influxPassword <influxdb password> \  
--influxDatabase <influxdb database> \  
--influxMeasurement <influxdb measurement>
```
