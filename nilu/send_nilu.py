""" Code to retrieve data from Nilu and publish it on a Mosquitto broker """
#!/usr/bin/python3

import json
import datetime
import time
import argparse
import requests
import paho.mqtt.client as mqtt
from icecream import ic

class HttpRequest:
    """Class to handle http requests"""
    def __init__(self, user_agent):
        self.user_agent = user_agent
        self.headers = requests.utils.default_headers()
        self.headers.update({'User-Agent': f'Private use only - {self.user_agent}'})
        self.http_response_raw = ""
        self.data_to_transform = ""
        self.transformed_data = dict()
        self.dictionaries = dict()
        self.keys = ""

    def get_data(self, url):
        """Method to make a http request and return a raw response"""
        self.http_response_raw = requests.get(url, headers=self.headers).json()
        ic()
        ic(self.http_response_raw)
        return self.http_response_raw

    def transform_data(self, data_to_transform):
        """
        Method to transform data from Nilu
        See for reference:
        https://luftkvalitet.miljodirektoratet.no/maalestasjon/Kirkeveien
        https://api.nilu.no/
        https://www.eea.europa.eu/themes/air/air-quality/resources/air-quality-map-thresholds#toc-13
        """
        self.data_to_transform = data_to_transform
        self.transformed_data = dict()

        for self.dictionaries in self.data_to_transform:

            for self.keys in self.dictionaries.keys():

                if self.dictionaries[self.keys] == "PM10":
                    self.transformed_data.update({"airquality_pm10" : self.dictionaries["value"]})
                    ic()
                    ic(self.transformed_data["airquality_pm10"])

                if self.dictionaries[self.keys] == "PM2.5":
                    self.transformed_data.update({"airquality_pm25" : self.dictionaries["value"]})
                    ic()
                    ic(self.transformed_data["airquality_pm25"])

                if self.dictionaries[self.keys] == "NO2":
                    self.transformed_data.update({"airquality_no2" : self.dictionaries["value"]})
                    ic()
                    ic(self.transformed_data["airquality_no2"])

        ic()
        ic(self.transformed_data)
        return self.transformed_data

class Mqtt:
    """Class to prepare messages and interact with Mosquitto messagebroker"""
    def __init__(self, mqtt_host, mqtt_port, mqtt_topic, mqtt_client_id):
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.mqtt_topic = mqtt_topic
        self.mqtt_client_id = mqtt_client_id
        self.mqtt_client = mqtt.Client(self.mqtt_client_id)
        self.prepared_message = ""

    def prepare_message(self, payload, serial):
        """Method to prepare message that will be sent"""
        self.prepared_message = payload
        self.prepared_message.update({"serial" : serial})
        self.prepared_message.update({"recordTime" : datetime.datetime.now().strftime(DATEFORMAT)})
        ic()
        ic(self.prepared_message)
        return self.prepared_message

    def send_message(self, message):
        """Method to send message via a Mosquitto message broker"""
        self.mqtt_client.connect(self.mqtt_host, self.mqtt_port)
        self.mqtt_client.publish(self.mqtt_topic, json.dumps(message))
        ic()
        ic(message)

class Controller:
    """Class to control the program"""
    def __init__(self, control_parameters):
        self.control_parameters = control_parameters
        self.error_timer = 0
        self.error_counter = 0
        self.validate_payload = ""
        self.serial = self.get_serial_number()
        self.now = ""
        self.main_loop()

    def main_loop(self):
        """Method to manage the program"""
        while self.error_counter <= 5:
            self.now = datetime.datetime.now().strftime(DATEFORMAT)

            print(f'{self.now}: error_counter is at {self.error_counter}, max is 5\n\
                     error_timer is at {round(self.error_timer/60)} minutes')

            try:
                nilu = HttpRequest(self.control_parameters.user_agent)
                nilu.get_data(self.control_parameters.url)
                nilu.transform_data(nilu.http_response_raw)
                self.validate_payload_nilu(nilu.transformed_data)
                broker_client = Mqtt(self.control_parameters.mqtt_host,\
                                    self.control_parameters.mqtt_port,\
                                    self.control_parameters.mqtt_topic,\
                                    self.control_parameters.mqtt_client_id)
                broker_client.prepare_message(nilu.transformed_data, self.serial)
                ic()

            except Exception:
                print(f'{self.now}: An error occured during retrieving and processing of data..')
                self.error_timer = self.error_timer + 1800
                self.error_counter = self.error_counter + 1
                print(f'{self.now}: Adjusting error_counter to {self.error_counter}\n\
                     Pausing for {round(self.error_timer/60)} minutes')
                ic()
                ic(self.error_counter)
                ic(self.error_timer)
                time.sleep(self.error_timer)

            else:
                try:
                    broker_client.send_message(broker_client.prepared_message)
                    print(f'{self.now}: Sent this message: {broker_client.prepared_message}')
                    print(f'{self.now}: Pausing program for 20 minutes...')
                    ic()
                    self.error_timer = 0
                    self.error_counter = 0
                    time.sleep(1200)

                except Exception:
                    print(f'{self.now}: An error occured during communication with MQTT..')
                    self.error_timer = self.error_timer + 1800
                    self.error_counter = self.error_counter + 1
                    print(f'{self.now}: Adjusting error_counter to {self.error_counter}\n\
                         Pausing for {round(self.error_timer/60)} minutes')
                    ic()
                    ic(self.error_counter)
                    ic(self.error_timer)
                    time.sleep(self.error_timer)

        while True:
            self.now = datetime.datetime.now().strftime(DATEFORMAT)
            print(f'{self.now}: Max errors exceeded, program has terminated...')
            ic()
            time.sleep(7200)

    def get_serial_number(self):
        """Get Raspberry Pi serial number to use as ID"""
        try:
            with open("/proc/cpuinfo", "r") as self.file:
                for self.line in self.file:
                    if self.line[0:6] == "Serial":
                        self.serial = self.line.split(":")[1].strip()
            ic(self.serial)
            return self.serial

        except Exception:
            self.serial = "0"
            return self.serial

    def validate_payload_nilu(self, transformed_data):
        """Method to check that payload contains at least one value"""
        self.validate_payload = transformed_data.copy()
        self.validate_payload.popitem()
        ic()
        del self.validate_payload

def read_parameters():
    """
    Function for reading variables for the script,
    for more on argparse, refer to https://zetcode.com/python/argparse/
    """
    parser = argparse.ArgumentParser(description="Publish Nilu values over mqtt")
    parser.add_argument("--debug", type=str,\
         help="Flag to enable or disable icecream debug", required=True)
    parser.add_argument("--user_agent", type=str,\
         help="email to identify with API owner", required=True)
    parser.add_argument("--url", type=str,\
         help="URL to API which will handle the request", required=True)
    parser.add_argument("--mqtt_host", type=str,\
         help="Hostname of MQTT server", required=True)
    parser.add_argument("--mqtt_port", type=int,\
         help="Port of MQTT server", required=True)
    parser.add_argument("--mqtt_topic", type=str,\
         help="MQTT topic to publish", required=True)
    parser.add_argument("--mqtt_client_id", type=str,\
         help="ClientID of the sending MQTT client", required=True)
    args = parser.parse_args()
    ic()
    ic(args)
    return args

if __name__ == "__main__":

    DATEFORMAT = "%d.%m.%Y %H:%M:%S"
    print(f'{datetime.datetime.now().strftime(DATEFORMAT)}: Starting program...')
    PARAMETERS = read_parameters()

    if PARAMETERS.debug == "yes":
        print(f'{datetime.datetime.now().strftime(DATEFORMAT)}: Debug mode')
        ic()
    elif PARAMETERS.debug == "no":
        ic()
        ic.disable()
        print(f'{datetime.datetime.now().strftime(DATEFORMAT)}: Debug deactivated')

    Controller(PARAMETERS)
