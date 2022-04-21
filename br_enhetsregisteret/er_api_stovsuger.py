"""Kode for å hente overordnede enheter fra Enhetsregisteret"""
#!/usr/bin/python3

import json
import requests
from icecream import ic

PAGECOUNTER = 0
NACE_CODES = "86, 87, 88"
JSON_DUMP = dict()

def read_parameters():
    """Function to read parameters from command line"""


def read_naeringcodes():
    """Function to read naering codes from specified file"""


def make_httprequest(NACE_CODES, PAGECOUNTER):
    """Function to make the API call"""
    return requests.get(f'https://data.brreg.no/enhetsregisteret/api/enheter?naeringskode={NACE_CODES}&page={PAGECOUNTER}', headers=requests.utils.default_headers()).json()

def parse_httpresponse():
    """Function to parse data from BR endpoint"""


def update_exportobject(key, value):
    """Function to update export object"""
    JSON_DUMP.update({key:value})

def dump_exportobject(exportobject):
    """Function to write export object to file"""
    with open('api_stovsuger_ut.json', 'w') as outfile:
        json.dump(exportobject, outfile)

#Main program
print(f'Treff på for næringskode(r) {NACE_CODES}:')
datainfo = make_httprequest(NACE_CODES, PAGECOUNTER)
print(f'Totalt antall elementer: {datainfo.get("page").get("totalElements")}, totalt antall sider: {datainfo.get("page").get("totalPages")}')

#Get total pages to use as counter
totalpages = datainfo.get("page").get("totalPages")

while PAGECOUNTER < totalpages:
    content = make_httprequest(NACE_CODES, PAGECOUNTER)
    print(f'Hentet data fra side: {content.get("page").get("number")+1} of {totalpages}')
    update_exportobject(PAGECOUNTER, content.get("_embedded").get("enheter"))
    print("Oppdaterte datadump")
    PAGECOUNTER = PAGECOUNTER+1

print("Skriver til fil..")
dump_exportobject(JSON_DUMP)
