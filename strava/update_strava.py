#!/usr/bin/env python3
"""Module to update gear in Strava activities"""

from pprint import pprint
import traceback
import time
import json
from datetime import datetime, timedelta
import argparse
from requests_oauthlib import OAuth2Session

class FileHandler:
    """Class to handle files"""
    def __init__(self, oauth_file, gear_file):
        self.oauth_file = oauth_file
        self.gear_file = gear_file
        self.token = dict()
        self.extra = dict()
        self.gear = dict()
        self.token_loader()
        self.gear_loader()

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

    def gear_loader(self):
        """Method to read gear data from file"""
        self.gear = json.load(open(self.gear_file, 'r'))

class Strava:
    """Class to interact with Strava API"""
    def __init__(self, oauth_file, gear_file):
        self.files = FileHandler(oauth_file, gear_file)
        self.json_response = ""
        self.client = None
        self.counter_updated = 0
        self.counter_skipped = 0
        self.counter_failed = 0
        self.process_broken = False

    def create_authenticated_session (self):
        """Method to create an authenticated session with the Strava API"""
        token_refresh_url = "https://www.strava.com/oauth/token"

        if self.files.token["expires_at"] < datetime.now().timestamp():
            print(f'{current_time()}: Access token expired at {datetime.fromtimestamp(self.files.token["expires_at"])}. Refreshing tokens')

            try:
                self.client = OAuth2Session(self.files.extra["client_id"], token=self.files.token)
                self.files.token = self.client.refresh_token(token_refresh_url, refresh_token=self.files.token["refresh_token"], **self.files.extra)
                self.files.token_saver()
                self.files.token_loader()

            except Exception:
                print(f'{current_time()}: An error occured refreshing tokens. Info about the error: ')
                self.process_broken = True
                traceback.print_exc()

        if self.files.token["expires_at"] > datetime.now().timestamp():
            try:
                print(f'{current_time()}: Access token valid. Expires at {datetime.fromtimestamp(self.files.token["expires_at"])}, in {datetime.fromtimestamp(self.files.token["expires_at"]) - datetime.now()}')
                self.client = OAuth2Session(self.files.extra["client_id"], token=self.files.token)

            except Exception:
                print(f'{current_time()}: An error occured creating authenticated session. Info about the error: ')
                self.process_broken = True
                traceback.print_exc()

    def get_activities(self):
        """Method to authenticate and get data from Strava API"""
        if self.process_broken is False:
            cutoff_date_after = (datetime.now() - timedelta(days=3))
            cutoff_date_before = (datetime.now() + timedelta(days=1))
            protected_resource = f"https://www.strava.com/api/v3/athlete/activities?before={cutoff_date_before.timestamp()}&after={cutoff_date_after.timestamp()}&page=1&per_page=200"

            try:
                raw_response = self.client.get(protected_resource)
                print(f'{current_time()}: API Status: {raw_response.status_code} - {raw_response.reason}')
                self.json_response = raw_response.json()
                print(f'{current_time()}: Attempting to fetch Strava activities after {cutoff_date_after.strftime("%d.%m.%Y")} and before {cutoff_date_before.strftime("%d.%m.%Y")}')
                if raw_response.status_code != 200:
                    self.process_broken = True

            except Exception:
                print(f'{current_time()}: An error occured during protected resource API call. Info about the error: ')
                self.process_broken = True
                traceback.print_exc()

    def process_activites(self):
        """Method to prepare API call of type post"""
        if self.process_broken is False:
            for activities in self.json_response:

                try:
                    print(f'\n{current_time()}: Processing activity with id {activities["id"]} from {str(activities["start_date_local"][:10])}, with start time {str(activities["start_date_local"][11:19])}. Current key activity information:')
                    try:
                        print(f'Bike information: {self.files.gear[activities["gear_id"]]} ({activities["gear_id"]})')
                    except Exception:
                        print(f'Bike with gearid {activities["gear_id"]} is not in dictionary')
                    finally:
                        print(f'Activity name: {activities["name"]}')
                        print(f'Activity type: {activities["type"]}')
                        print(f'Commute: {(activities["commute"])}')
                        print(f'Distance: {round(float(activities["distance"]/1000),2)} km')

                    #Section to be specified by user. Add elif blocks as needed
                    if activities["sport_type"] == "Ride" and "Ride" in activities["name"] and round(float(activities["distance"]/1000),2) < 20:
                        variables = {"name": "Bysykling",
                                "commute": True,
                                "gear_id": "b3450507",
                                "description": "Auto-updated"
                        }
                        print("Information to be updated in activity:")
                        pprint(variables, indent=4)

                        try:
                            print(f'Bike with gearid {variables["gear_id"]} has name {self.files.gear[variables["gear_id"]]}')
                        except Exception:
                            print(f'Bike with gearid {variables["gear_id"]} is not in dictionary')

                        self.make_api_call(activities["id"], variables)

                    else:
                        print("Activity did not match criteria, nothing will be updated")
                        self.counter_skipped = self.counter_skipped+1

                except Exception:
                    self.counter_failed = self.counter_failed+1
                    self.process_broken = True
                    print('\nAn unexpected error ocurred processing the following activity:')
                    print(f'Id: {activities["id"]}, date: {str(activities["start_date_local"][:10])}, start time: {str(activities["start_date_local"][11:19])}')
                    print('More info about the error:')
                    traceback.print_exc()

            print(f'\n{current_time()}: Fetched activities: {len(self.json_response)}')
            print(f'{current_time()}: Updated activities: {self.counter_updated}')
            print(f'{current_time()}: Skipped activities: {self.counter_skipped}')
            print(f'{current_time()}: Failed activities:  {self.counter_failed}')

    def make_api_call(self, activity_id, payload):
        """Doc string"""
        if self.process_broken is False:
            protected_resource = f'https://www.strava.com/api/v3/activities/{activity_id}'
            put_response = self.client.put(protected_resource, payload)

            if put_response.status_code == 200:
                print(f'API Status {put_response.status_code} - {put_response.reason}. Activity update success')
                self.counter_updated = self.counter_updated+1
            else:
                print(f'API Status {put_response.status_code} - {put_response.reason}. Activity update failure')
                self.counter_failed = self.counter_failed+1

class Controller:
    """Class to control the program"""

    def __init__(self, control_parameters):
        self.control_parameters = control_parameters
        self.main_loop()

    def main_loop(self):
        """Method to handle program logic"""
        strava = Strava(self.control_parameters.oauth_file, self.control_parameters.gear_file)

        while True:

            try:
                strava.create_authenticated_session()
                strava.get_activities()
                strava.process_activites()
                print(f'\n{current_time()}: Next program run in 120 minutes...')
                print("\n")
                strava.counter_updated = 0
                strava.counter_skipped = 0
                strava.counter_failed = 0
                strava.process_broken = False
            except Exception:
                print(f'{current_time()}: An unexpected error occured during main loop. Info about the error:')
                traceback.print_exc()
                print("\n")
            finally:
                time.sleep(7200)

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
    parser.add_argument("--gear_file", type=str,
                        help="File with gear data", required=True)
    args = parser.parse_args()

    return args

if __name__ == "__main__":

    print(f'{current_time()}: Starting program...')
    PARAMETERS = read_parameters()
    Controller(PARAMETERS)
