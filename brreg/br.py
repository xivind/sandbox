"""Code to retrieve and parse data from Enhetsregisteret"""
#!/usr/bin/python3

import json
import requests
from icecream import ic

def read_parameters():
    """Function to read parameters from command line"""
    pass

def read_naeringcodes():
    """Function to read naering codes from specified file"""
    pass

def make_httprequest():
    """Function to retrieve data from BR endpoint"""
    pass

def parse_httpresponse():
    """Function to parse data from BR endpoint"""
    pass

def update_exportobject():
    """Function to update export object"""
    pass

def dump_exportobject():
    """Function to write export object to file"""
    pass

NAERINGCODES = "87.1"
JSON_DUMP = dict()

http_response_raw = requests.get(f'https://data.brreg.no/enhetsregisteret/api/enheter?naeringskode={NAERINGCODES}&page=0', headers=requests.utils.default_headers()).json()

print(f'Query overview for naeringcodes {NAERINGCODES}:')
print(f'Total elements: {http_response_raw.get("page").get("totalElements")}, total pages: {http_response_raw.get("page").get("totalPages")}')


totalpages = http_response_raw.get("page").get("totalPages")
pagecounter = 0



while pagecounter < totalpages:
    http_response_raw = requests.get(f'https://data.brreg.no/enhetsregisteret/api/enheter?naeringskode={NAERINGCODES}&page={pagecounter}', headers=requests.utils.default_headers()).json()
    print(f'Getting data from page: {http_response_raw.get("page").get("number")+1} of {totalpages}')
    content = http_response_raw.get("_embedded").get("enheter")
    JSON_DUMP.update({pagecounter:content})
    pagecounter = pagecounter+1


with open('outfile.json', 'w') as outfile:
    json.dump(JSON_DUMP, outfile)
