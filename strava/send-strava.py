#!/usr/bin/env python3

import json
import time
import requests
import argparse
import paho.mqtt.client as mqtt
from icecream import ic
from datetime import datetime, timedelta


# Reading variables for the script
# For more on argparse, refer to https://zetcode.com/python/argparse/
def argsReader():
    parser = argparse.ArgumentParser(description="Publish Strava values over mqtt")
    parser.add_argument("--debug", type=str, help="Flag to enable or disable icecream debug",required=True)
    parser.add_argument("--tokens", type=str, help="Access and refresh tokens for oauth",required=True)
    parser.add_argument("--mqttHost", type=str, help="Hostname of MQTT server",required=True)
    parser.add_argument("--mqttPort", type=int, help="Port of MQTT server",required=True)
    parser.add_argument("--mqttTopic", type=str, help="MQTT topic to publish",required=True)
    parser.add_argument("--mqttClientID", type=str, help="ClientID of the sending MQTT client",required=True)
    args = parser.parse_args()
    ic()
    ic(args)
    return args

# Get Raspberry Pi serial number to use as ID
def get_serial_number():
    with open("/proc/cpuinfo", "r") as f:
        for line in f:
            if line[0:6] == "Serial":
                ic()
                ic(line.split(":")[1].strip())
                return line.split(":")[1].strip()

def getDates():
  afterDateInput = datetime.now() - timedelta(days=3) 
  beforeDateInput = datetime.now() + timedelta(days=1)  
  afterDateEpoch = afterDateInput.timestamp()
  beforeDateEpoch = beforeDateInput.timestamp()
  dateList = []
  dateList.insert(0, afterDateEpoch)
  dateList.insert(1, beforeDateEpoch)
  ic()
  ic(dateList)
  return dateList

def readSecrets():
  secrets = json.load(open(args.tokens,'r'))
  clientID = secrets['clientId']
  clientSecret = secrets['clientSecret']
  accessToken = secrets['accessToken']
  refreshToken = secrets['refreshToken']
  ic()
  ic(clientID, clientSecret, accessToken, refreshToken)
  return clientID, clientSecret, accessToken, refreshToken

def getNewAccessToken(clientID, clientSecret, refreshToken):
  tokenURL = "https://www.strava.com/oauth/token"
  response = requests.post(url = tokenURL,data =\
    {'client_id': clientID,'client_secret': clientSecret,'grant_type': 'refresh_token','refresh_token': refreshToken})
  responseJson = response.json()
  writeSecrets(clientID, clientSecret, str(responseJson['access_token']), str(responseJson['refresh_token']))
  ic()

# Write new access tokens to file
def writeSecrets(clientID, clientSecret, accessToken,refreshToken):
  secrets = {}
  secrets['clientId'] = clientID
  secrets['clientSecret'] = clientSecret
  secrets['accessToken'] = accessToken
  secrets['refreshToken'] = refreshToken
  FileObj = open(args.tokens,'w')
  FileObj.write(json.dumps(secrets))
  FileObj.close()
  ic()
  ic(accessToken, refreshToken)

# Make the API call
def MakeAPICall(clientID, clientSecret, accessToken,refreshToken, stravaResource):
  session = requests.Session()
  session.headers.update({'Authorization': f'Bearer {accessToken}'})
  response = session.get(stravaResource)
  ic()
  
  if response.status_code == 401:
      print(f'{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Access token expired, getting new')
      getNewAccessToken(clientID, clientSecret, refreshToken)
      ic()
      return False, TokenRefreshedOK
  else:
      print(f'{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Access token passed')
      FullResponse = response.json()
      ic()
      return True, FullResponse

# Main program
args = argsReader()
serial = get_serial_number()
TokenRefreshedOK = "Token refreshed OK"
ErrorInAPI = "An error occured during API call that wasnt expected"
errorCounter = 0
errorTimer = 0

print(f'{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Starting program...')

# Enable / disable debugging
if args.debug == "yes":
  print(f'{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Debug mode')
  ic()
elif args.debug == "no":
  ic.disable()
  ic()
  print(f'{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Debug deactivated')

# Main loop, until errorcounter is exceeded
while errorCounter <= 5:
  print(f'{datetime.now().strftime("%d.%m.%Y %H:%M:%S")} errorCounter is at {errorCounter}, max is 5. errorTimer is at {round(errorTimer/60)} minutes')

  # Get latest version of sercrets from file
  clientID, clientSecret, accessToken, refreshToken = readSecrets()
  
  # Get dates to retrieve rides
  dateList = getDates()
  stravaResource = f'https://www.strava.com/api/v3/athlete/activities?before={dateList[1]}&after={dateList[0]}&page=1&per_page=200'
  print(f'{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Retrieving rides after {datetime.fromtimestamp(dateList[0]).strftime("%Y-%m-%d")} and before {datetime.fromtimestamp(dateList[1]).strftime("%Y-%m-%d")}')
    
  # Make the API call
  APICallOK, APIResponse = MakeAPICall(clientID, clientSecret, accessToken, refreshToken, stravaResource)

  # Prepare and send message to database

  if APICallOK:
    
    try:
      json_object = APIResponse
      
      # The json_object is a list of dictionaries.
      # The first loop iterates through the list and the second loop iterates through the dictionaries.
      
      for dictionaries in json_object:
        
        values = {}
        
        for keys in dictionaries.keys():
          
          if keys == "start_date_local":
            values["recordTime"] = dictionaries[keys]
            
          if keys == "elapsed_time":
            values["elapsedTime"] = round(float((dictionaries[keys]/60)/60),2)
          
          if keys == "distance":
            values["distance"] = round(float(dictionaries[keys]/1000),2)
          
          if keys == "total_elevation_gain":
            values["totalElevation"] = int(dictionaries[keys])

          if keys == "average_speed":
            values["averageSpeed"] = round(float(dictionaries[keys]*3.6),1)
          
          if keys == "achievement_count":
            values["achievements"] = dictionaries[keys]
          
        values["serial"] = serial
        
        client1=mqtt.Client(args.mqttClientID)
        client1.connect(args.mqttHost,args.mqttPort)
        client1.publish(args.mqttTopic, json.dumps(values))
        print(f'{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Sent this message: {values}')
        ic()
        ic(values)
      
      errorCounter = 0
      errorTimer = 0
      print(f'{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Pausing program for 30 minutes...')
      ic()
      time.sleep(1800)
      
    except:
      errorCounter = errorCounter + 1
      errorTimer = errorTimer + 1800
      print(f'{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: General error, no message sent...')
      print(f'{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Adjusting errorCounter to {errorCounter} and pausing for {round(errorTimer/60)} minutes')
      ic()
      ic(errorCounter)
      ic(errorTimer)
      time.sleep(errorTimer)
      
  else:
    if (APIResponse == TokenRefreshedOK):
        print(f'{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Refreshed the access token. Good to go!')
        errorCounter = 0
        errorTimer = 0
        ic()
        ic(APIResponse)
    else:
        errorCounter = errorCounter + 1
        errorTimer = errorTimer + 1800
        print(f'{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: {ErrorInAPI}')
        print(f'{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Adjusting errorCounter to {errorCounter} and pausing for {round(errorTimer/60)} minutes')
        ic()
        time.sleep(errorTimer)

while(True):
  print(f'{datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Max errors exceeded, program has terminated...')
  time.sleep(7200)