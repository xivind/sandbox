#!/usr/bin/python3

import requests
import json
import datetime
import time
import argparse
import paho.mqtt.client as mqtt
from icecream import ic

# Reading variables for the script
# For more on argparse, refer to https://zetcode.com/python/argparse/
def argsReader():
    parser = argparse.ArgumentParser(description="Publish Yr values over mqtt")
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

#Get data from yr
def read_yr():
    try:
        url = 'https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=59.9379&lon=10.7568'
        headers = requests.utils.default_headers()
        headers.update({'User-Agent': f'Import to private weather station - {args.userAgent}'})
        response = requests.get(url, headers=headers).json()
        now = response['properties']['timeseries'][0]
        data_out_city = now['data']['instant']['details']
        ic(headers)

        url = 'https://api.met.no/weatherapi/locationforecast/2.0/compact?lat=60.0734&lon=10.7070'
        headers = requests.utils.default_headers()
        headers.update({'User-Agent': f'Import to private weather station - {args.userAgent}'})
        response = requests.get(url, headers=headers).json()
        now = response['properties']['timeseries'][0]
        data_out_forest = now['data']['instant']['details']
        ic(headers)

        values = {}
        citytemp = data_out_city['air_temperature']
        values["citytemp"] = int(citytemp)
        forestemp = data_out_forest['air_temperature']
        values["foresttemp"] = int(forestemp)
        city_humidity = data_out_city['relative_humidity']
        values["city_humidity"] = int(city_humidity)
        forest_humidity = data_out_forest['relative_humidity']
        values["forest_humidity"] = int(forest_humidity)
        wind_direction_city = data_out_city['wind_from_direction']
        values["wind_direction_city"] = int(wind_direction_city)
        wind_speed_city = data_out_city['wind_speed']
        values["wind_speed_city"] = int(wind_speed_city)
        wind_direction_forest = data_out_forest['wind_from_direction']
        values["wind_direction_forest"] = int(wind_direction_forest)
        wind_speed_forest = data_out_forest['wind_speed']
        values["wind_speed_forest"] = int(wind_speed_forest)
        values["serial"] = serial
        values["recordTime"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ic()
        ic(values)
        return values
    
    except:
        print('General error in function read_yr. Returning empty values.')
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
    
    values = read_yr()
    
    try:
        validateYr = values["citytemp"]
        validateYr = values["foresttemp"]
        validateYr = values["wind_direction_city"] 
        validateYr = values["wind_speed_city"] 
        validateYr = values["wind_direction_forest"] 
        validateYr = values["wind_speed_forest"]

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