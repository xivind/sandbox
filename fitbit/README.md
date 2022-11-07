# About
Bla bla, content and short description

Create the container that retrieves data from Fitbit with the command below. This container only retrieves data from Fitbit and sends it to the mqtt broker. It does not need to persist data. The commands must be run from the directory that contains `Dockerfile` and `requirements.txt`

`docker build -t fitbit .`

```
docker run -d \  
--name=fitbit \  
-e TZ=Europe/Stockholm \  
-v /<path on host to directory containing file with tokens>:/secrets \  
--restart unless-stopped \  
fitbit \  
./send-fitbit.py \  
--debug no \  
--tokens /secrets/<name of filen with tokens> \  
--mqttHost <mosquitto host> \  
--mqttPort 1883 \  
--mqttTopic <mosquitto topic> \  
--mqttClientID <mosquitto clientID>
```

Use https://dev.fitbit.com/build/reference/web-api/troubleshooting-guide/oauth2-tutorial/ to get token, remember to use pkce

Remember sequence in SQL-sscriptet, variables in payload must match order of columns in SQL

Info about the SQL connector: https://pynative.com/python-mysql-insert-data-into-database-table/
Exception handling: https://overiq.com/mysql-connector-python-101/exception-handling-in-connector-python/

Docker bridge: https://stackoverflow.com/questions/52146056/how-to-delete-disable-docker0-bridge-on-docker-startup, maybe not in this doc? Also in archimate..

Fitbit requires authentication with OAuth2. In the script we are using here, the tokens are handled through a json file, which must look as following. 

`{"AccToken": "", "RefToken": "", "ClientId": "", "ClientSecret": ""}`

[Thanks to Pauls Geek Dad Blog](https://pdwhomeautomation.blogspot.com/2016/01/fitbit-api-access-using-oauth20-and.html) for pointing us in the right direction with python and OAuth2 also.

