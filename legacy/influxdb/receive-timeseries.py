#!/usr/bin/env python3
import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient
import datetime
import json
import argparse

# Reading variables for the script
# For more on argparse, refer to https://zetcode.com/python/argparse/
def argsReader():
    parser = argparse.ArgumentParser(description="Publish enviroplus values over mqtt")
    parser.add_argument("--mqttHost", type=str, help="Hostname of MQTT server",required=True)
    parser.add_argument("--mqttPort", type=int, help="Port of MQTT server",required=True)
    parser.add_argument("--mqttKeepalive", type=int, help="Keep alive in seconds for the MQTT connection",required=True)
    parser.add_argument("--mqttTopic", type=str, help="MQTT topic to subscribe",required=True)
    parser.add_argument("--influxHost", type=str, help="Hostname of InfluxDB server",required=True)
    parser.add_argument("--influxPort", type=str, help="Port of the InfluxDB server",required=True)
    parser.add_argument("--influxUser", type=str, help="User for InfluxDB",required=True)
    parser.add_argument("--influxPassword", type=str, help="Password for InfluxDB",required=True)
    parser.add_argument("--influxDatabase", type=str, help="Database of the InfluxDB server",required=True)
    parser.add_argument("--influxMeasurement", type=str, help="Measurement table to place recordings",required=True)
    args = parser.parse_args()
    return args

# The callback for when the client receives a CONNACK response from the server
def on_connect(client, userdata, flags, resultCode):
    print("Connected with result code "+str(resultCode))
    client.subscribe(args.mqttTopic)
    print(f'Subscribed to topic {args.mqttTopic}')

# The callback for when a PUBLISH message is received from the server
def on_message(client, userdata, msg):
    messageTime = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    json_preprocess = json.loads(msg.payload)
    influxdbimport = []
    influxdbimport_dict = {'measurement': args.influxMeasurement,
                    'tags': {'serial': json_preprocess['serial']},
                    'time': str(json_preprocess['recordTime']),
                    'fields': {}}
    
    for datapoint in json_preprocess:
        if datapoint != 'serial':
            if datapoint != 'recordTime':
                influxdbimport_dict['fields'][datapoint] = float(json_preprocess[datapoint])
    
    influxdbimport.append(influxdbimport_dict)
    
    dbclient = InfluxDBClient(host=args.influxHost, port=args.influxPort, username=args.influxUser, password=args.influxPassword)
    dbclient.switch_database(args.influxDatabase)
    dbclient.write_points(influxdbimport, time_precision='s')

    print(f'{messageTime}: Wrote the following measurements to InfluxDB:\n{influxdbimport}')

# Main program
print(f'Container started at {datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")}')
args = argsReader()
print("Running program with the following arguments:")
for keys, values in vars(args).items():
    print(f'{keys} - {values}')
print("*********")
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(args.mqttHost, args.mqttPort, args.mqttKeepalive)

client.loop_forever()
