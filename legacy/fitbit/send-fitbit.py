import base64
import json
import datetime
import time
import argparse
import requests
import paho.mqtt.client as mqtt
from icecream import ic

# Reading variables for the script
# For more on argparse, refer to https://zetcode.com/python/argparse/
def argsReader():
    parser = argparse.ArgumentParser(description="Publish Fitbit values over mqtt")
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

# Get acess tokens
def GetNewAccessToken(RefToken):
  TokenURL = "https://api.fitbit.com/oauth2/token"
  Session = requests.Session()
  encodedPrep = f'{OAuthTwoClientID}:{ClientOrConsumerSecret}'
  encodedAll = base64.b64encode(bytes(encodedPrep, "utf8"))
  Session.headers.update({'Authorization': f'Basic {encodedAll.decode()}'})
  Session.headers.update({'Content-Type':'application/x-www-form-urlencoded'})
  Payload = f'grant_type=refresh_token&refresh_token={RefToken}'
  Response = Session.post(TokenURL,data=Payload)
  ResponseJSON = Response.json()
  WriteConfig(str(ResponseJSON['access_token']), str(ResponseJSON['refresh_token']))
  ic()

# Write new access tokens to file
def WriteConfig(AccToken,RefToken):
  ConfigJson['AccToken'] = AccToken
  ConfigJson['RefToken'] = RefToken
  FileObj = open(args.tokens,'w')
  FileObj.write(json.dumps(ConfigJson))
  FileObj.close()
  ic()
  ic(AccToken, RefToken)

# Make the API call
def MakeAPICall(urlFromDict,AccToken,RefToken):
  Session = requests.Session()
  Session.headers.update({'Authorization': f'Bearer {AccToken}'})
  Response = Session.get(urlFromDict)
  
  if Response.status_code == 401:
      print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Access token expired, getting new')
      GetNewAccessToken(RefToken)
      ic()
      return False, TokenRefreshedOK
  else:
      print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Access token passed')
      FullResponse = Response.json()
      ic()
      return True, FullResponse

def read_fitbit_activity(json_object):
  values = {}
  values["activityFloors"] = json_object["summary"]["floors"]
  values["activitySteps"] = json_object["summary"]["steps"]
  values["recordTime"] = str(dateparam+"T14:05:00Z")
  ic()
  ic(values)
  return values

def read_fitbit_weight(json_object):
  values = {}
  values["weightKg"] = json_object["weight"][0]["weight"]
  values["weightBmi"] = json_object["weight"][0]["bmi"]
  values["weightFat"] = json_object["weight"][0]["fat"]
  values["recordTime"] = str(dateparam+"T14:03:00Z")
  ic()
  ic(values)
  return values

def read_fitbit_water(json_object):
  values = {}
  values["water"] = json_object["summary"]["water"]
  values["recordTime"] = str(dateparam+"T14:02:00Z")
  ic()
  ic(values)
  return values

def read_fitbit_sleep(json_object):
  values = {}
  values["sleepTotalTimeInBed"] = json_object["summary"]["totalTimeInBed"]
  values["sleepTotalMinutesAsleep"] = json_object["summary"]["totalMinutesAsleep"]
  values["sleepStagesDeep"] = json_object["summary"]["stages"]["deep"]
  values["sleepStagesLight"] = json_object["summary"]["stages"]["light"]
  values["sleepStagesRem"] = json_object["summary"]["stages"]["rem"]
  values["sleepStagesWake"] = json_object["summary"]["stages"]["wake"]
  values["recordTime"] = str(dateparam+"T14:01:00Z")
  ic()
  ic(values)
  return values

def read_fitbit_hr(json_object):
  values = {}
  values["hrResting"] = json_object["activities-heart"][0]["value"]["restingHeartRate"]
  values["hrFatburn"] = json_object['activities-heart'][0]['value']['heartRateZones'][1]['minutes']
  values["hrCardio"] = json_object['activities-heart'][0]['value']['heartRateZones'][2]['minutes']
  values["hrPeak"] = json_object['activities-heart'][0]['value']['heartRateZones'][3]['minutes']
  values["recordTime"] = str(dateparam+"T14:04:00Z")
  ic()
  ic(values)
  return values

# Main program
args = argsReader()
serial = get_serial_number()
TokenRefreshedOK = "Token refreshed OK"
ErrorInAPI = "An error occured during API call that wasnt expected"
errorCounter = 0
errorTimer = 0

print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Starting program...')

# Enable / disable debugging
if args.debug == "yes":
  print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Debug mode')
  ic()
elif args.debug == "no":
  ic()
  ic.disable()
  print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Debug deactivated')

# Main loop, until errorcounter is exceeded
while errorCounter <= 5:
  print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: errorCounter is at {errorCounter}, max is 5. errorTimer is at {round(errorTimer/60)} minutes')

  # Fitbit URLs to use for the API call
  dateparam = datetime.datetime.now().strftime("%Y-%m-%d")
  urlDict = {"activities" : "https://api.fitbit.com/1/user/-/activities/date/"+dateparam+".json",\
              "weight" : "https://api.fitbit.com/1/user/-/body/log/weight/date/" +dateparam+".json",\
              "water" : "https://api.fitbit.com/1/user/-/foods/log/date/" +dateparam+".json",\
              "sleep" : "https://api.fitbit.com/1.2/user/-/sleep/date/" +dateparam+".json",\
              "heartrate" : "https://api.fitbit.com/1/user/-/activities/heart/date/"+dateparam+"/1d.json"\
            }

  # Fitbit functions to write values to dict
  functionDict = {"activities" : read_fitbit_activity,\
              "weight" : read_fitbit_weight,\
              "water" : read_fitbit_water,\
              "sleep" : read_fitbit_sleep,\
              "heartrate" : read_fitbit_hr\
            }

  print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Retrieving fitbit data for {dateparam}')

  for key in urlDict:

    # Get latet version of secrets from file
    ConfigJson = json.load(open(args.tokens,'r'))
    AccessToken = ConfigJson['AccToken']
    RefreshToken = ConfigJson['RefToken']
    OAuthTwoClientID = ConfigJson['ClientId']
    ClientOrConsumerSecret = ConfigJson['ClientSecret']
    ic()
    ic(AccessToken, RefreshToken)

    APICallOK, APIResponse = MakeAPICall(urlDict[key], AccessToken, RefreshToken)

    if APICallOK:
      try:
        json_object = APIResponse
        function = functionDict[key]
        values = function(json_object)
        values["serial"] = serial
        client1=mqtt.Client(args.mqttClientID)
        client1.connect(args.mqttHost,args.mqttPort)
        client1.publish(args.mqttTopic, json.dumps(values))
        print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Sent this message: {values}')
        ic()

      # This is a non-critical error, typically due to no data recorded. Do not increase errorCounter og errorTimer
      except(IndexError, KeyError, TypeError):
        print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Dictionary error, probably no data recorded. No message sent...')

      errorCounter = 0
      errorTimer = 0
      ic()
      ic(errorCounter)  
      ic(errorTimer)
      
    else:
      if (APIResponse == TokenRefreshedOK):
          print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Refreshed the access token. Good to go!')
          errorCounter = 0
          errorTimer = 0
          ic()
          ic(errorCounter)  
          ic(errorTimer)
          ic(APIResponse)
          
      else:
          errorCounter = errorCounter + 1
          errorTimer = errorTimer + 1800
          print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: {ErrorInAPI}')
          print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Adjusting errorCounter to {errorCounter} and pausing for {round(errorTimer/60)} minutes')
          ic()
          ic(errorCounter)
          ic(errorTimer)
          time.sleep(errorTimer)

  print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Pausing for 30 minutes...')
  time.sleep(1800)

while(True):
  print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Max errors exceeded, program has terminated...')
  time.sleep(7200)