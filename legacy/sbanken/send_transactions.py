#!/usr/bin/env python3
"""Module to get transaction from Sbanken and send them on a MQTT broker"""

import json
import argparse
import datetime
import traceback
import time
import urllib.parse
from pprint import pprint
import paho.mqtt.client
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

class Sbanken:
    """Class for Sbanken. Handles authentication and requests"""

    def __init__(self, oauth_file):
        self.client_id = ""
        self.client_secret = ""
        self.customer_id = ""
        self.account_id = ""
        self.session = ""
        self.raw_response = dict()
        self.oauth_file = oauth_file
        self.read_oauth_options()

    def read_oauth_options(self):
        """Method to read oauth options from file"""
        secrets = json.load(open(self.oauth_file, 'r'))
        self.client_id = urllib.parse.quote(secrets['client_id'])
        self.client_secret = urllib.parse.quote(secrets['client_secret'])
        self.customer_id = urllib.parse.quote(secrets['customer_id'])
        self.account_id = urllib.parse.quote(secrets['account_id'])

    def create_authenticated_http_session(self):
        """Method to handle the oauth2 protocol"""
        oauth2_client = BackendApplicationClient(client_id=self.client_id)
        self.session = OAuth2Session(client=oauth2_client)
        self.session.fetch_token(
            token_url='https://auth.sbanken.no/identityserver/connect/token',
            client_id=self.client_id,
            client_secret=self.client_secret
            )

    def get_transactions(self):
        """Method to make http request. Default is the last 30 days. See Sbanken docs"""
        endDate = datetime.datetime.today()
        startDate = endDate - datetime.timedelta(days=10)

        print(f"Fetching transactions between {startDate.strftime('%Y-%m-%d')} and {endDate.strftime('%Y-%m-%d')}")
        
        response_object = self.session.get(
            f"https://publicapi.sbanken.no/apibeta/api/v2/Transactions/archive/{self.account_id}?startDate={startDate.strftime('%Y-%m-%d')}&endDate={endDate.strftime('%Y-%m-%d')}&length=300",
            headers={'customerId': self.customer_id}
            )
    
        self.raw_response = response_object.json()

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

    def prepare_message(self, data_to_transform, card_provider):
        """Method to prepare visa message to be sent via a Mosquitto message broker"""
        self.transformed_data.clear()

        self.transformed_data.update({"unique_id": str(data_to_transform["cardDetails"]["transactionId"])})
        self.transformed_data.update({"record_time": str(data_to_transform["cardDetails"]["purchaseDate"])})
        self.transformed_data.update({"merchant_name": str(data_to_transform["cardDetails"]["merchantName"])})
        self.transformed_data.update({"merchant_category": str(data_to_transform["cardDetails"]["merchantCategoryDescription"])})
        self.transformed_data.update({"amount": int(data_to_transform["amount"]*-1)})
        self.transformed_data.update({"card_provider": str(card_provider)})

    def prepare_legacy_message(self, data_to_transform, card_provider):
        """Method to prepare legacy visa message to be sent via a Mosquitto message broker"""
        self.transformed_data.clear()

        interestDate =  datetime.datetime.strptime(data_to_transform["interestDate"], "%Y-%m-%dT%H:%M:%S") - datetime.timedelta(days=1)

        self.transformed_data.update({"unique_id": str(data_to_transform["transactionId"])})
        self.transformed_data.update({"record_time": datetime.datetime.strftime(interestDate, "%Y-%m-%dT%H:%M:%S")})
        self.transformed_data.update({"merchant_name": str(data_to_transform["text"])})
        self.transformed_data.update({"merchant_category": "Legacy visa"})
        self.transformed_data.update({"amount": int(data_to_transform["amount"]*-1)})
        self.transformed_data.update({"card_provider": str(card_provider)})

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
        sbanken = Sbanken(self.control_parameters.oauth_file)
        broker_client = Mqtt(self.control_parameters.mqtt_host,
                             self.control_parameters.mqtt_port,
                             self.control_parameters.mqtt_topic,
                             self.control_parameters.mqtt_client_id)

        while True:

            now = datetime.datetime.now().strftime(DATEFORMAT)
            cutoff_date = datetime.datetime.today() - datetime.timedelta(days=7)
            total_transactions = 0
            archived_visa_transactions = 0
            archived_visa_legacy_transactions = 0
            other_transactions = 0
            sent_archived_visa_transactions = 0
            sent_archived_visa_legacy_transactions = 0
            process_broken = False

            try:
                print(f'\n{now}: Attempting authentication')
                sbanken.create_authenticated_http_session()

            except:
                print(f'{now}: Authentication failed')
                process_broken = True

            if process_broken is False:
                try:
                    print(f'{now}: Making API call')
                    sbanken.get_transactions()
                    transactions = sbanken.raw_response.get("items")

                except:
                    print(f'{now}: API call failed')
                    process_broken = True

            if process_broken is False:
                try:
                    for record in transactions:

                        total_transactions = total_transactions + 1

                        if record["source"] == 1 and record["cardDetailsSpecified"] is True:
                            archived_visa_transactions = archived_visa_transactions + 1

                            try:
                                broker_client.prepare_message(record, self.control_parameters.card_provider)
                                broker_client.send_message(broker_client.transformed_data)
                                print(f'\n{now}: Sent archived visa transcation:')
                                pprint(broker_client.transformed_data, indent=4)
                                sent_archived_visa_transactions = sent_archived_visa_transactions + 1

                            except:
                                print(f'\n{now}: An error occured preparing or sending visa message for record:')
                                pprint(record, indent=4)

                        elif record["source"] == 1 and record["cardDetailsSpecified"] is False and record["transactionType"] == "VARER":
                            archived_visa_legacy_transactions = archived_visa_legacy_transactions + 1

                            try:
                                if datetime.datetime.strptime(record["interestDate"], "%Y-%m-%dT%H:%M:%S") < cutoff_date:
                                    print(f'\n{now}: Archived visa legacy transaction older than cutoff date {datetime.datetime.strftime(cutoff_date, "%d.%m.%Y")}')
                                    broker_client.prepare_legacy_message(record, self.control_parameters.card_provider)
                                    broker_client.send_message(broker_client.transformed_data)
                                    print(f'{now}: Sent archived visa legacy transcation:')
                                    pprint(broker_client.transformed_data, indent=4)
                                    sent_archived_visa_legacy_transactions = sent_archived_visa_legacy_transactions + 1
                                else:
                                    print(f'\n{now}: Archived visa legacy transaction newer than cutoff date {datetime.datetime.strftime(cutoff_date, "%d.%m.%Y")}')
                                    print(f'{now}: Skipping transcation:')
                                    broker_client.prepare_legacy_message(record, self.control_parameters.card_provider)
                                    pprint(broker_client.transformed_data, indent=4)

                            except:
                                print(f'\n{now}: An error occured preparing or sending visa legacy message for record:')
                                pprint(record, indent=4)

                        else:
                            print(f'\n{now}: Record is not an archived visa transaction:')
                            pprint(record, indent=4)
                            other_transactions = other_transactions + 1

                    print(f'\n{now}: API call returned {total_transactions} archived transactions:')
                    print(f'{now:}: Found {archived_visa_transactions} archived visa transactions')
                    print(f'{now:}: Found {archived_visa_legacy_transactions} archived transactions that are legacy visa')
                    print(f'{now:}: Found {other_transactions} archived transactions that are non-visa')
                    print(f'{now:}: Sent {sent_archived_visa_legacy_transactions} archived visa legacy transactions')
                    print(f'{now:}: Sent {sent_archived_visa_transactions} archived visa transactions')

                except:
                    print(f'\n{now}: An unexpected error occured. Info about the error: ')
                    traceback.print_exc()

            print(f'\n{now}: Pausing for eight hours...')
            time.sleep(28800)

def read_parameters():
    """
    Function for reading variables for the script,
    for more on argparse, refer to https://zetcode.com/python/argparse/
    """
    parser = argparse.ArgumentParser(
        description="Configuration parameters")
    parser.add_argument("--oauth_file", type=str,
                        help="File with oauth user data", required=True)
    parser.add_argument("--card_provider", type=str,
                        help="Name of card provider", required=True)
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
