"""Code to retrieve data from Yr and publish it on a Mosquitto broker"""
#!/usr/bin/python3

import traceback
import json
import datetime
import time
import argparse
import requests
import paho.mqtt.client
from icecream import ic

class System:
    """Class for Raspberry Pi"""

    def get_serial_number(self):
        """Get Raspberry Pi serial number to use as ID"""
        serial = ""
        try:
            with open("/proc/cpuinfo", "r") as file:
                for line in file:
                    if line[0:6] == "Serial":
                        serial = line.split(":")[1].strip()
            ic(serial)
            return serial

        except Exception:
            serial = "0"
            return serial

class HttpRequest:
    """Class to handle http requests"""

    def __init__(self, url_file, user_agent):
        self.urls = json.load(open(url_file, 'r'))
        self.user_agent = user_agent
        self.headers = requests.utils.default_headers()
        self.headers.update(
            {'User-Agent': f'Private use only - {self.user_agent}'})
        ic()
        ic(self.urls)

    def get_data(self, url):
        """Method to make a http request and return a raw response"""
        http_response_raw = \
            requests.get(url, headers=self.headers).json()[
                'properties']['timeseries'][0]['data']['instant']['details']
        ic()
        ic(http_response_raw)
        return http_response_raw

class Data:
    """Class to handle data objects"""

    def __init__(self):
        self.transformed_data = dict()
        self.merged_data = dict()
        self.prepared_message = dict()
        self.serial = ""

    def store_serial(self, serial):
        """Method to store serial number of pi"""
        self.serial = serial

    def transform_data(self, data_to_transform):
        """Method to transform data from Yr"""

        self.transformed_data.clear()

        for keys in data_to_transform:

            if keys == "air_temperature":
                self.transformed_data.update({"air_temperature":
                                              int(data_to_transform["air_temperature"])})

            if keys == "relative_humidity":
                self.transformed_data.update({"relative_humidity":
                                              int(data_to_transform["relative_humidity"])})

            if keys == "wind_from_direction":
                self.transformed_data.update({"wind_from_direction":
                                              int(data_to_transform["wind_from_direction"])})

            if keys == "wind_speed":
                self.transformed_data.update({"wind_speed":
                                              int(data_to_transform["wind_speed"])})

        ic()
        ic(self.transformed_data)

    def merge_data(self, keys):
        """Method to tag the data according to the resource file"""
        for untagged_keys in self.transformed_data:

            self.merged_data.update({f"{keys}_{untagged_keys}":\
                f"{self.transformed_data.get(untagged_keys)}"})
            ic()

        ic(self.merged_data)

    def validate_data(self, unvalidated_data):
        """Method to check that payload contains at least one value"""
        validate_data = unvalidated_data.copy()
        validate_data.popitem()
        ic()
        del validate_data

    def prepare_message(self):
        """Method to prepare message that will be sent"""
        self.prepared_message = self.merged_data
        self.prepared_message.update({"serial": self.serial})
        self.prepared_message.update({"recordTime":\
             datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                                    )
        ic()
        ic(self.prepared_message)

class Mqtt(paho.mqtt.client.Client):
    """Class to interact with Mosquitto messagebroker"""

    def __init__(self, mqtt_host, mqtt_port, mqtt_topic, mqtt_client_id):
        super().__init__()
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.mqtt_topic = mqtt_topic
        self.mqtt_client_id = mqtt_client_id

    def send_message(self, message):
        """Method to send message via a Mosquitto message broker"""
        self.connect(self.mqtt_host, self.mqtt_port)
        self.publish(self.mqtt_topic, json.dumps(message))
        ic()
        ic(message)

class Controller:
    """Class to control the program"""

    def __init__(self, control_parameters):
        self.control_parameters = control_parameters
        self.main_loop()

    def main_loop(self):
        """Method to manage the program"""
        yr = HttpRequest(self.control_parameters.url_file, self.control_parameters.user_agent)
        datastore = Data()
        system = System()
        broker_client = Mqtt(self.control_parameters.mqtt_host,
                             self.control_parameters.mqtt_port,
                             self.control_parameters.mqtt_topic,
                             self.control_parameters.mqtt_client_id)
        error_timer = 0
        error_counter = 0
        now = ""
        datastore.store_serial(system.get_serial_number())

        while True:
            now = datetime.datetime.now().strftime(DATEFORMAT)

            print(f'{now}: error_counter is at {error_counter}, max is 5\n\
                     error_timer is at {round(error_timer/60)} minutes')

            try:

                for keys in yr.urls.keys():

                    datastore.transform_data(yr.get_data(yr.urls.get(keys)))
                    datastore.merge_data(keys)
                    ic()

                datastore.validate_data(datastore.merged_data)
                datastore.prepare_message()

            except Exception:
                print(
                    f'{now}: An error occured during retrieving and processing of data..')
                error_timer = error_timer + 1800
                error_counter = error_counter + 1
                print(f'{now}: Adjusting error_counter to {error_counter}\n\
                     Pausing for {round(error_timer/60)} minutes')
                ic()
                ic(error_counter)
                ic(error_timer)
                print(f'{now}: **** Info about the error ****')
                traceback.print_exc()
                time.sleep(error_timer)

            else:
                try:
                    broker_client.send_message(datastore.prepared_message)
                    print(f'{now}: Sent this message: {datastore.prepared_message}')
                    print(f'{now}: Pausing program for 20 minutes...')
                    ic()
                    error_timer = 0
                    error_counter = 0
                    time.sleep(1200)

                except Exception:
                    print(
                        f'{now}: An error occured during communication with MQTT..')
                    error_timer = error_timer + 1800
                    error_counter = error_counter + 1
                    print(f'{now}: Adjusting error_counter to {error_counter}\n\
                         Pausing for {round(error_timer/60)} minutes')
                    ic()
                    ic(error_counter)
                    ic(error_timer)
                    print(f'{now}: **** Info about the error ****')
                    traceback.print_exc()
                    time.sleep(error_timer)

            if error_counter > 5:
                now = datetime.datetime.now().strftime(DATEFORMAT)
                print(f'{now}: Max errors exceeded, halting program...')
                ic()
                time.sleep(14400)
                now = datetime.datetime.now().strftime(DATEFORMAT)
                print(f'{now}: Resetting error counter and restarting program...')
                error_counter = 0

def read_parameters():
    """
    Function for reading variables for the script,
    for more on argparse, refer to https://zetcode.com/python/argparse/
    """
    parser = argparse.ArgumentParser(description="Publish Yr values over mqtt")
    parser.add_argument("--debug", type=str,
                        help="Flag to enable or disable icecream debug", required=True)
    parser.add_argument("--user_agent", type=str,
                        help="email to identify with API owner", required=True)
    parser.add_argument("--url_file", type=str,
                        help="Name and path to the file that contains the URLs to use", required=True)
    parser.add_argument("--mqtt_host", type=str,
                        help="Hostname of MQTT server", required=True)
    parser.add_argument("--mqtt_port", type=int,
                        help="Port of MQTT server", required=True)
    parser.add_argument("--mqtt_topic", type=str,
                        help="MQTT topic to publish", required=True)
    parser.add_argument("--mqtt_client_id", type=str,
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
    