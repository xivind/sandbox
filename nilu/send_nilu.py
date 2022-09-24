#!/usr/bin/env python3
"""Module to retrieve data from Nilu and publish it on a Mosquitto broker"""

import json
import argparse
import datetime
import traceback
import time
from pprint import pprint
import requests
import paho.mqtt.client

class Nilu:
    """Class for Nilu. Handles authentication and requests"""

    def __init__(self, user_agent):
        self.user_agent = user_agent
        self.headers = requests.utils.default_headers()
        self.headers.update(
            {'User-Agent': f'Private use only - {self.user_agent}'})
        self.raw_response = dict()

    def get_data(self, url):
        """Method to make a http request and return a raw response"""
        self.raw_response = requests.get(url, headers=self.headers).json()

class Mqtt(paho.mqtt.client.Client):
    """Class to interact with Mosquitto messagebroker"""

    def __init__(self, mqtt_host, mqtt_port, mqtt_topic, mqtt_client_id):
        super().__init__()
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.mqtt_topic = mqtt_topic
        self.mqtt_client_id = mqtt_client_id
        self.transformed_data = dict()
        self.message = ""

    def prepare_message(self, data_to_transform):
        """Method to prepare message to be sent via a Mosquitto message broker"""
        self.transformed_data.clear()

        for dictionaries in data_to_transform:

            for keys in dictionaries.keys():

                if dictionaries[keys] == "PM10":
                    self.transformed_data.update(
                        {"airquality_pm10": dictionaries["value"]})

                if dictionaries[keys] == "PM2.5":
                    self.transformed_data.update(
                        {"airquality_pm25": dictionaries["value"]})

                if dictionaries[keys] == "NO2":
                    self.transformed_data.update(
                        {"airquality_no2": dictionaries["value"]})

        self.transformed_data.update({"record_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

    def send_message(self, message):
        """Method to send message via a Mosquitto message broker"""
        self.message = json.dumps(message)
        self.connect(self.mqtt_host, self.mqtt_port)
        self.publish(self.mqtt_topic, self.message)

class Controller:
    """Class to control the program"""

    def __init__(self, control_parameters):
        self.control_parameters = control_parameters
        self.main_loop()

    def main_loop(self):
        """Method to handle program logic"""
        nilu = Nilu(self.control_parameters.user_agent)
        broker_client = Mqtt(self.control_parameters.mqtt_host,
                             self.control_parameters.mqtt_port,
                             self.control_parameters.mqtt_topic,
                             self.control_parameters.mqtt_client_id)

        while True:

            now = datetime.datetime.now().strftime(DATEFORMAT)
            process_broken = False

            try:
                print(f'{now}: Making API call')
                nilu.get_data(self.control_parameters.url)

            except:
                print(f'{now}: API call failed. Info about the error:')
                traceback.print_exc()
                process_broken = True

            if process_broken is False:
                try:
                    broker_client.prepare_message(nilu.raw_response)

                except:
                    print(f'{now}: An error occured preparing message for record:')
                    pprint(nilu.raw_response, indent=4)
                    print(f'{now}: Info about the error:')
                    traceback.print_exc()
                    process_broken = True

            if process_broken is False:
                try:
                    broker_client.send_message(broker_client.transformed_data)
                    print(f'{now}: Sent the following data as message:')
                    pprint(broker_client.transformed_data, indent=4)

                except:
                    print(f'{now}: An error occured sending message with record:')
                    pprint(broker_client.transformed_data, indent=4)
                    print(f'{now}: Info about the error:')
                    traceback.print_exc()

            print(f'\n{now}: Next program run in 60 minutes...')
            time.sleep(3600)

def read_parameters():
    """
    Function for reading variables for the script,
    for more on argparse, refer to https://zetcode.com/python/argparse/
    """
    parser = argparse.ArgumentParser(
        description="Configuration parameters")
    parser.add_argument("--user_agent", type=str,
                        help="email to identify with API owner", required=True)
    parser.add_argument("--url", type=str,
                        help="URL to API which will handle the request", required=True)
    parser.add_argument("--mqtt_host", type=str,
                        help="Hostname of MQTT server", required=True)
    parser.add_argument("--mqtt_port", type=int,
                        help="Port of MQTT server", required=True)
    parser.add_argument("--mqtt_topic", type=str,
                        help="MQTT topic to publish", required=True)
    parser.add_argument("--mqtt_client_id", type=str,
                        help="ClientID of the sending MQTT client", required=True)
    args = parser.parse_args()

    return args

if __name__ == "__main__":

    DATEFORMAT = "%d.%m.%Y %H:%M:%S"
    print(f'{datetime.datetime.now().strftime(DATEFORMAT)}: Starting program...')
    PARAMETERS = read_parameters()

    Controller(PARAMETERS)
