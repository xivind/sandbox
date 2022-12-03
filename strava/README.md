# About
Bla bla, content and short description


Archimate-model

## Update activities 

## Manual

## Automatic

Create the container that retrieves data from Strava with the command below. This container only retrieves data from Strava and sends it to the mqtt broker. It does not need to persist data. The commands must be run from the directory that contains `Dockerfile` and `requirements.txt`. The script here is quite rudimentary in regards to the handling of data. Benji Knights Johnson has a better approach, using Pandas, that is described [in an article on medium](https://medium.com/swlh/using-python-to-connect-to-stravas-api-and-analyse-your-activities-dummies-guide-5f49727aac86).

Refer to trekking.. (youtoube and script), to create the initital tokens

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


Short intro about what the code does and why
The Python code in this folder consists of four modules:
- send_strava.py and send_strava_manual.py:   
- update_strava.py: updates recent activities based on user defined criteria.
- oauth2_helper.py: BLA BLA

# Info about executables and parameter files in this folder
- `send_strava.py`
Uses Strava activities API to retrieve rides for a specified athlete for the last three days. Once the data is received, the module modifies the data structure and publishes the data to a MQTT topic. Contains loops so it runs repeatedly, e.g. in a container or through systemd
- `send_strava_manual.py`
Same as `send_strava.py`, execpt that it accepts a date range as input and runs only once
- `update_strava.py`
Uses Strava activities API to update recent activities based on user defined criteria
- `oauth_helper.py`
Uses Strava oauth endpoint to retrieve initial access tokens
- `create-container-send-strava.sh`
Sends commands to the Docker engine to create image and container and to run the container with the `send_strava.py` module
- `create-container-update-strava.sh`
Sends commands to the Docker engine to create image and container and to run the container with the `update_strava.py` module
- `send-strava-requirements.txt`
Information about Python packages to be included in the docker image for the `send_strava.py` module
- `update-strava-requirements.txt`
Information about Python packages to be included in the docker image for the `update_strava.py` module
- `strava_tokens.json`
User specific information needed to authorize with Strava's APIs
- `strava_gear.json`
User specific information needed to update gear in a given ride
- `send-strava.Dockerfile`
Instructions to the docker daemon for building image for the `send_strava.py` module
- `update-strava.Dockerfile`
Instructions to the docker daemon for building image for the `update_strava.py` module

# How to use the code
There are a few things that must be in place for these modules to work:
- You must have access to Sbanken's archived transactions API. Sbanken has a [developer portal](https://sbanken.no/bruke/utviklerportalen/) that provides all the necessary instructions to get started.
- Although it will work to run the script manually, its best to run it either through [systemd](https://en.wikipedia.org/wiki/Systemd) or Docker. This will ensure that the script runs continously and you will also get some built-in error handling, e.g. automatic restart if something unexpected happens. The code in this folder assumes Docker engine is running.
- The script publishes message to a [MQTT](https://mqtt.org/) topic. MQTT is freely available and can for example be run as a [Docker container](https://hub.docker.com/_/eclipse-mosquitto). 


>*I made this code to hone my Python skills and to experiment with Sbanken's API. As such there may be flaws and choices in the code that could represent issues with information security. Sbankens API accesses production data, i.e. actual data/money, so keep this in mind if you would like to use this code*

**Complete the following steps to get the code running CHANGE NAME**
1. Copy the files in this folder to your environment. Best would be to clone it with Git, so you receive updates when the code is improved
2. Login to Sbankes developer portal and retrieve client id, client secret, customer id and account id. Note that account id is not the same as account number. You may need to query Sbankens customer API to get the account id. Enter this information into the file `sbanken_oauth.json`. Make sure no one else has access to this file.
3. Modify the shell script `create-container-finance.sh` according to suit your environment, e.g. with information about the MQTT broker.
4. Run the shell script `create-container-finance.sh`.


![Overview of main components](diagram.png)

The script only sends data to the MQTT topic. Only creativity limits what is possible to do with that data. For me, I am interested in figuring out why my money somehow seem to disappear in thin air. As such I have created another piece of code that subscribes to the topic, writes the data to MariaDB and visualises it in Grafana. Information about that code will follow later.
![Visualisation of archived transactions](visualization.png)

**Complete the following steps to get the code running CHANGE NAME**