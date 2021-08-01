""" Code to retrieve data from Yr and publish it on a Mosquitto broker """
#!/usr/bin/python3

import traceback
import json
import datetime
import time
import argparse
import requests
import paho.mqtt.client as mqtt
from icecream import ic

class ResourceFile:
    """Class to handle resource URLs"""""
    def __init__(self, url_file):
        self.url_file = url_file
        self.urls = self.read_urls()

    def read_urls(self):
        """Method to read content of json file and create dictionary"""
        self.urls = json.load(open(self.url_file, 'r'))
        ic()
        ic(self.urls)
        return self.urls

class HttpRequest:
    """Class to handle http requests"""
    def __init__(self, user_agent):
        self.user_agent = user_agent
        self.headers = requests.utils.default_headers()
        self.headers.update({'User-Agent': f'Private use only - {self.user_agent}'})
        self.http_response_filtered = dict()
        self.data_to_transform = dict()
        self.transformed_data = dict()
        self.keys = ""

    def get_data(self, url):
        """Method to make a http request and return a raw response"""
        self.http_response_filtered = \
            requests.get(url, headers=self.headers).json()\
                         ['properties']['timeseries'][0]['data']['instant']['details']
        ic()
        ic(self.http_response_filtered)
        return self.http_response_filtered

    def transform_data(self, data_to_transform):
        """
        Method to transform data from Yr
        """
        self.data_to_transform = dict(data_to_transform)
        self.transformed_data = dict()

        for self.keys in self.data_to_transform:

            if self.keys == "air_temperature":
                self.transformed_data.update({"air_temperature" : \
                    int(self.data_to_transform["air_temperature"])})

            if self.keys == "relative_humidity":
                self.transformed_data.update({"relative_humidity" : \
                    int(self.data_to_transform["relative_humidity"])})

            if self.keys == "wind_from_direction":
                self.transformed_data.update({"wind_from_direction" : \
                    int(self.data_to_transform["wind_from_direction"])})

            if self.keys == "wind_speed":
                self.transformed_data.update({"wind_speed" : \
                    int(self.data_to_transform["wind_speed"])})

        ic()
        ic(self.transformed_data)
        return self.transformed_data

class Payload:
    """Class to deal with the payload"""
    def __init__(self):
        self.validated_payload = ""
        self.transformed_data = dict()
        self.merged_payload = dict()
        self.tagged_data = dict()
        self.payload = dict()

    def validate_payload(self, transformed_data):
        """Method to check that payload contains at least one value"""
        self.validated_payload = transformed_data.copy()
        self.validated_payload.popitem()
        ic()
        del self.validated_payload

    def tag_payload(self, transformed_data, keys):
        """Method to tag the data according to the resource file"""
        self.transformed_data = dict(transformed_data)
        self.tagged_data = dict()

        for untagged_keys in self.transformed_data:

            self.tagged_data.update({f"{keys}_{untagged_keys}":\
                                     f"{self.transformed_data.get(untagged_keys)}"\
                                    })
            ic()

        ic(self.tagged_data)
        return self.tagged_data

    def merge_payload(self, payload):
        """"Method to merge two or more payloads"""
        self.payload = dict(payload)
        self.merged_payload.update(self.payload)
        ic()
        ic(self.merged_payload)
        return self.merged_payload

class Mqtt:
    """Class to prepare messages and interact with Mosquitto messagebroker"""
    def __init__(self, mqtt_host, mqtt_port, mqtt_topic, mqtt_client_id):
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.mqtt_topic = mqtt_topic
        self.mqtt_client_id = mqtt_client_id
        self.mqtt_client = mqtt.Client(self.mqtt_client_id)
        self.prepared_message = dict()

    def prepare_message(self, payload, serial):
        """Method to prepare message that will be sent"""
        self.prepared_message = payload
        self.prepared_message.update({"serial" : serial})
        self.prepared_message.update(\
            {"recordTime" : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                                    ) 
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
        self.serial = self.get_serial_number()
        self.now = ""
        self.main_loop()

    def main_loop(self):
        """Method to manage the program"""
        resource_file = ResourceFile(self.control_parameters.url_file)
        payload = Payload()

        while self.error_counter <= 5:
            self.now = datetime.datetime.now().strftime(DATEFORMAT)

            print(f'{self.now}: error_counter is at {self.error_counter}, max is 5\n\
                     error_timer is at {round(self.error_timer/60)} minutes')

            try:
                yr_resource = HttpRequest(self.control_parameters.user_agent)

                for self.keys in resource_file.urls:

                    yr_resource.get_data(resource_file.urls.get(self.keys))
                    yr_resource.transform_data(yr_resource.http_response_filtered)
                    payload.validate_payload(yr_resource.transformed_data)
                    payload.tag_payload(yr_resource.transformed_data, self.keys)
                    payload.merge_payload(payload.tagged_data)
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
                print(f'{self.now}: **** Info about the error ****')
                traceback.print_exc()
                time.sleep(self.error_timer)

            else:
                try:
                    broker_client = Mqtt(self.control_parameters.mqtt_host,
                                         self.control_parameters.mqtt_port,
                                         self.control_parameters.mqtt_topic,
                                         self.control_parameters.mqtt_client_id
                                        )

                    broker_client.prepare_message(payload.merged_payload, self.serial)
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
                    print(f'{self.now}: **** Info about the error ****')
                    traceback.print_exc()
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


def read_parameters():
    """
    Function for reading variables for the script,
    for more on argparse, refer to https://zetcode.com/python/argparse/
    """
    parser = argparse.ArgumentParser(description="Publish Yr values over mqtt")
    parser.add_argument("--debug", type=str,\
         help="Flag to enable or disable icecream debug", required=True)
    parser.add_argument("--user_agent", type=str,\
         help="email to identify with API owner", required=True)
    parser.add_argument("--url_file", type=str,\
         help="Name and path to the file that contains the URLs to use", required=True)
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
