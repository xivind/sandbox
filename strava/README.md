# About
Bla bla, content and short description


Archimate-model

## Update activities 

## Manual

## Automatic

Create the container that retrieves data from Strava with the command below. This container only retrieves data from Strava and sends it to the mqtt broker. It does not need to persist data. The commands must be run from the directory that contains `Dockerfile` and `requirements.txt`. The script here is quite rudimentary in regards to the handling of data. Benji Knights Johnson has a better approach, using Pandas, that is described [in an article on medium](https://medium.com/swlh/using-python-to-connect-to-stravas-api-and-analyse-your-activities-dummies-guide-5f49727aac86).

Refer to trekking.. (youtoube and script)

`docker build -t strava .`

```
docker run -d \  
--name=strava \  
-e TZ=Europe/Stockholm \  
-v /<path on host to directory containing file with tokens>:/secrets \  
--restart unless-stopped \  
strava \  
./send-strava.py \  
--debug no \  
--tokens /secrets/<name of filen with tokens> \  
--mqttHost <mosquitto host> \  
--mqttPort 1883 \  
--mqttTopic <mosquitto topic> \  
--mqttClientID <mosquitto clientID>
```

Strava requires authentication with OAuth2. It looks complicated, but is fairly straight forward to configure if you follow [Stravas step-by-step guide](https://developers.strava.com/docs/getting-started/#oauth). In the script we are using here, the tokens are handled through a json file, which must look as following.

`{"clientId": "", "clientSecret": "", "accessToken": "", "refreshToken": ""}`
