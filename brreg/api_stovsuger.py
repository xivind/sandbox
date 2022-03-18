"""Code to retrieve and parse data from Enhetsregisteret"""
#!/usr/bin/python3

import json
import requests
from icecream import ic

PAGECOUNTER = 0
NAERINGCODES = "86.1, 87.1" #Oppgi liste med komma mellom verdier
JSON_DUMP = dict()

def read_parameters():
    """Function to read parameters from command line"""
    pass

def read_naeringcodes():
    """Function to read naering codes from specified file"""
    pass

def make_httprequest(NAERINGCODES, PAGECOUNTER):
    """Function to make the API call"""
    return requests.get(f'https://data.brreg.no/enhetsregisteret/api/enheter?naeringskode={NAERINGCODES}&page={PAGECOUNTER}', headers=requests.utils.default_headers()).json()

def parse_httpresponse():
    """Function to parse data from BR endpoint"""
    pass

def update_exportobject(key, value):
    """Function to update export object"""
    JSON_DUMP.update({key:value})

def dump_exportobject(exportobject):
    """Function to write export object to file"""
    with open('api_stovsuger_ut.json', 'w') as outfile:
        json.dump(exportobject, outfile)

#Main program
print(f'Treff på for næringskode(r) {NAERINGCODES}:')
datainfo = make_httprequest(NAERINGCODES, PAGECOUNTER)
print(f'Totalt antall elementer: {datainfo.get("page").get("totalElements")}, totalt antall sider: {datainfo.get("page").get("totalPages")}')

"""Get total pages to use as counter"""
totalpages = datainfo.get("page").get("totalPages")

while PAGECOUNTER < totalpages:
    content = make_httprequest(NAERINGCODES, PAGECOUNTER)
    print(f'Hentet data fra side: {content.get("page").get("number")+1} of {totalpages}')
    update_exportobject(PAGECOUNTER, content.get("_embedded").get("enheter"))
    print("Oppdaterte datadump")
    PAGECOUNTER = PAGECOUNTER+1

print("Skriver til fil..")
dump_exportobject(JSON_DUMP)

