"""Code to retrieve and parse data from Enhetsregisteret"""
#!/usr/bin/python3

from os.path import exist
import pandas as pd
import numpy as np
import requests
import urllib.request
import gzip
import io
import json

"""
OUTFILE = 'out.csv'

file_exists = exists(OUTFILE)

if file_exists == True:
         print("File exists")
else: 
        print("no exist")
"""


def get_dataset():

# Hente ut data fra BRREG
url_get = 'https://data.brreg.no/enhetsregisteret/api/enheter/lastned'
with urllib.request.urlopen(url_get) as response:
    encoding = response.info().get_param('charset', 'utf8')
    compressed_file = io.BytesIO(response.read())
    decompressed_file = gzip.decompress(compressed_file.read())
    json_str = json.loads(decompressed_file.decode('utf-8'))

# Lage pandas dataframe av json list
df2 = pd.json_normalize(json_str) 

# Henter ut relevante kolonner
df2 = df2[["Organisasjonsnummer", "Navn", 'Organisasjonsform.kode', "Organisasjonsform.beskrivelse", "Næringskode 1", "Næringskode 1.beskrivelse", "Postadresse.adresse", "Postadresse.kommune", "Registreringsdato i Enhetsregisteret", "Registrert i MVA-registeret"]]

# Konvertere datatyper til string
df3 = df2.astype(str)

# Liste med næringskoder for å filtrere
searchfor = ["86.101", "86.102", "86.103", "86.104"]

# Dataframe med filtrering på næringskoder i liste
nkode1 = df3[df3['naeringskode1.kode'].isin(searchfor)]
nkode2 = df3[df3['naeringskode2.kode'].isin(searchfor)]
nkode3 = df3[df3['naeringskode3.kode'].isin(searchfor)]

# Use pandas.concat() method to concat dataframes and ignore_index 
enheter = pd.concat([nkode1, nkode2, nkode3], ignore_index=True, sort=False)

#Skriver ut CSV
enheter.to_csv(OUTFILE) 
