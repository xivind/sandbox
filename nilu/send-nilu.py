#!/usr/bin/python3

import requests
import json
import datetime
import time
import argparse
import paho.mqtt.client as mqtt
from icecream import ic

#Use for reference
#https://luftkvalitet.miljodirektoratet.no/maalestasjon/Kirkeveien
#Developer docs at https://api.nilu.no/
#Air quality map https://www.eea.europa.eu/themes/air/air-quality/resources/air-quality-map-thresholds#toc-13

# Reading variables for the script
# For more on argparse, refer to https://zetcode.com/python/argparse/
def argsReader():
    parser = argparse.ArgumentParser(description="Publish Nilu values over mqtt")
    parser.add_argument("--debug", type=str, help="Flag to enable or disable icecream debug",required=True)
    parser.add_argument("--userAgent", type=str, help="email to identify with API owner",required=True)
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

#Get data from nilu
def read_nilu():
    try:
        url = 'https://api.nilu.no/aq/utd?stations=Kirkeveien&components=pm10;pm2.5;no2'
        headers = requests.utils.default_headers()
        headers.update({'User-Agent': f'Import to private weather station - {args.userAgent}'})
        response = requests.get(url, headers=headers).json()
        airquality = response[0:3]
        ic(headers)

        values = {}
        airquality_pm10 = airquality[0]['value']
        values["airquality_pm10"] = (airquality_pm10)
        airquality_pm25 = airquality[1]['value']
        values["airquality_pm25"] = (airquality_pm25)
        airquality_no2 = airquality[2]['value']
        values["airquality_no2"] = (airquality_no2)
        values["serial"] = serial
        values["recordTime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ic()
        ic(values)        
        return values
    
    except:
        print(f'General error in function read_nilu. Returning empty values.')
        values = {}
        ic()
        return values

# Main program
args = argsReader()
serial = get_serial_number()
errorCounter = 0
errorTimer = 0

print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Starting program...')

# Enable / disable debugging
if args.debug == "yes":
  print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Debug mode')
  ic()
elif args.debug == "no":
  ic.disable()
  ic()
  print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Debug deactivated')


while errorCounter <= 5:
    print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: errorCounter is at {errorCounter}, max is 5. errorTimer is at {round(errorTimer/60)} minutes')
    
    values = read_nilu()
    
    try:
        validateNilu = values["airquality_pm10"]
        validateNilu = values["airquality_pm25"]
        validateNilu = values["airquality_no2"]

        client1=mqtt.Client(args.mqttClientID)
        client1.connect(args.mqttHost,args.mqttPort)
        client1.publish(args.mqttTopic, json.dumps(values))
        print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Sent this message: {values}')
        
        errorCounter = 0
        errorTimer = 0
        print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Pausing program for 20 minutes...')
        ic()
        ic(values)
        time.sleep(1200)
    
    except:
        errorCounter = errorCounter + 1
        errorTimer = errorTimer + 1800
        print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: General error, no message sent...')
        print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Adjusting errorCounter to {errorCounter} and pausing for {round(errorTimer/60)} minutes')
        ic()
        ic(errorCounter)
        ic(errorTimer)
        time.sleep(errorTimer)
        

while(True):
    print(f'{datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}: Max errors exceeded, program has terminated...')
    time.sleep(7200)