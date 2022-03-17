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

NAERINGCODES = "86"

http_response_raw = requests.get(f'https://data.brreg.no/enhetsregisteret/api/enheter?naeringskode={NAERINGCODES}&page=0', headers=requests.utils.default_headers()).json()

print(f'Query overview for naeringcodes {naeringcodes}:')
print(f'Total elements: {http_response_raw.get("page").get("totalElements")}, total pages: {http_response_raw.get("page").get("totalPages")}')

#for items in http_response_raw.get("page").items():
 #   print(items)


totalpages = http_response_raw.get("page").get("totalPages")
pagecounter = 0

#Copy _embedded?

# Change to for-loop
while pagecounter <= totalpages:
    http_response_raw = requests.get(f'https://data.brreg.no/enhetsregisteret/api/enheter?naeringskode={naeringcodes}&page={pagecounter}', headers=requests.utils.default_headers()).json()
    print(f'Getting data from page: {http_response_raw.get("page").get("number")} of {totalpages}')
    pagecounter = pagecounter+1
    