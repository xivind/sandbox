#!/usr/bin/env python3
"""Module to get activities from Strava and send them on a MQTT broker"""

from pprint import pprint
import traceback
import json
import time
from datetime import datetime, timedelta
import argparse
from requests_oauthlib import OAuth2Session
import paho.mqtt.client

class Strava:
    """Class to interact with Strava API"""
    def __init__(self, oauth_file):
        self.token = dict()
        self.extra = dict()
        self.json_response = ""
        self.oauth_file = oauth_file

    def token_loader(self):
        """Method to read oauth options from file"""
        secrets_input = json.load(open(self.oauth_file, 'r'))
        self.token = {
             'access_token': secrets_input['access_token'],
             'refresh_token': secrets_input['refresh_token'],
             'token_type': secrets_input['token_type'],
             'expires_at': secrets_input['expires_at']

        }
        self.extra = {
            'client_id': secrets_input['client_id'],
            'client_secret': secrets_input['client_secret']
        }

    def token_saver(self):
        """Method to save oauth options to file"""
        secrets_output = self.token
        secrets_output['client_id'] = self.extra["client_id"]
        secrets_output['client_secret'] = self.extra["client_secret"]
        file_obj = open(self.oauth_file,'w')
        file_obj.write(json.dumps(secrets_output))
        file_obj.close()

    def get_data(self):
        """Method to authenticate and get data from Strava API"""
        self.token_loader()
        before_date_epoch = (datetime.now() + timedelta(days=1)).timestamp()
        after_date_epoch = (datetime.now() - timedelta(days=3)).timestamp()
        refresh_url = "https://www.strava.com/oauth/token"
        protected_url = f"https://www.strava.com/api/v3/athlete/activities?before={before_date_epoch}&after={after_date_epoch}&page=1&per_page=200"

        if self.token["expires_at"] < datetime.now().timestamp():
            print(f'{current_time()}: Access token expired at {datetime.fromtimestamp(self.token["expires_at"])}. Refreshing tokens')

            try:
                client = OAuth2Session(self.extra["client_id"], token=self.token)
                self.token = client.refresh_token(refresh_url, refresh_token=self.token["refresh_token"], **self.extra)
                self.token_saver()
                self.token_loader()

            except Exception:
                print(f'{current_time()}: An error occured refreshing tokens. Info about the error: ')
                traceback.print_exc()

        try:
            print(f'{current_time()}: Access token valid. Expires at {datetime.fromtimestamp(self.token["expires_at"])}, in {datetime.fromtimestamp(self.token["expires_at"]) - datetime.now()}')
            client = OAuth2Session(self.extra["client_id"], token=self.token)
            raw_response = client.get(protected_url)
            print(f'{current_time()}: API Status: {raw_response.status_code} - {raw_response.reason}')
            print(f'{current_time()}: Fetched Strava activities after {datetime.fromtimestamp(after_date_epoch).strftime("%d.%m.%Y")} and before {datetime.fromtimestamp(before_date_epoch).strftime("%d.%m.%Y")}')
            self.json_response = raw_response.json()

        except Exception:
            print(f'{current_time()}: An error occured during protected resource API call. Info about the error: ')
            traceback.print_exc()

class Mqtt(paho.mqtt.client.Client):
    """Class to interact with Mosquitto messagebroker"""
    def __init__(self, mqtt_host, mqtt_port, mqtt_topic, mqtt_client_id):
        super().__init__()
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.mqtt_topic = mqtt_topic
        self.mqtt_client_id = mqtt_client_id
        self.payload = dict()
        self.message = ""

    def prepare_message(self):
        """Method to prepare message to be sent via a Mosquitto message broker"""
        activity_counter = 0
        for activities in strava.json_response:

            try:
                self.payload.clear()
                self.payload.update({"id": int(activities["id"])})
                self.payload.update({"gear_id": str(activities["gear_id"])})
                self.payload.update({"name": str(activities["name"])})
                self.payload.update({"type": str(activities["type"])})
                self.payload.update({"location_country": str(activities["location_country"])})
                self.payload.update({"start_date_local": str(activities["start_date_local"]).replace("Z","")})
                self.payload.update({"elapsed_time": str(timedelta(seconds=activities["elapsed_time"]))})
                self.payload.update({"moving_time": str(timedelta(seconds=activities["moving_time"]))})
                self.payload.update({"distance": round(float(activities["distance"]/1000),2)})
                self.payload.update({"average_speed": round(float(activities["average_speed"]*3.6),1)})
                self.payload.update({"max_speed": round(float(activities["max_speed"]*3.6),1)})
                self.payload.update({"total_elevation_gain": int(activities["total_elevation_gain"])})
                self.payload.update({"achievement_count": int(activities["achievement_count"])})
                self.payload.update({"kudos_count": int(activities["kudos_count"])})
                self.payload.update({"commute": bool(activities["commute"])})
                if activities["has_heartrate"] is True:
                    self.payload.update({"average_heartrate": int(activities["average_heartrate"])})
                    self.payload.update({"max_heartrate": int(activities["max_heartrate"])})
                    self.payload.update({"suffer_score": int(activities["suffer_score"])})

                activity_counter = 1 + activity_counter

                self.send_message()
                print(f'\n{current_time()}: Sent Strava activity:')
                pprint(self.payload, indent=4)

            except Exception:
                print(f'\n{current_time()}: An error ocurred preparing or sending message:')
                pprint(self.payload, indent=4)
                print(f'{current_time()}: More info about the error:')
                traceback.print_exc()

        print(f'\n{current_time()}: Got {len(strava.json_response)} Strava activities')
        print(f'{current_time()}: Sent {activity_counter} Strava activities')

    def send_message(self):
        """Method to send message via a Mosquitto message broker"""
        self.message = json.dumps(self.payload)
        self.connect(self.mqtt_host, self.mqtt_port)
        self.publish(self.mqtt_topic, self.message)

def current_time():
    """Function to return current datetime formatted as string"""
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    return now

def read_parameters():
    """
    Function for reading variables for the script,
    for more on argparse, refer to https://zetcode.com/python/argparse/
    """
    parser = argparse.ArgumentParser(
        description="Configuration parameters")
    parser.add_argument("--oauth_file", type=str,
                        help="File with oauth user data", required=True)
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

    print(f'{current_time()}: Starting program...')
    PARAMETERS = read_parameters()
    strava = Strava(PARAMETERS.oauth_file)
    broker_client = Mqtt(PARAMETERS.mqtt_host,
                             PARAMETERS.mqtt_port,
                             PARAMETERS.mqtt_topic,
                             PARAMETERS.mqtt_client_id)
    while True:

        try:
            strava.get_data()
            broker_client.prepare_message()
            print(f'\n{current_time()}: Next program run in eight hours...')
            print("\n")
        except Exception:
            print(f'{current_time()}: An unexpected error occured during main loop. Info about the error:')
            traceback.print_exc()
            print("\n")
        finally:
            time.sleep(28800)
