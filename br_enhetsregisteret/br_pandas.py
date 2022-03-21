"""Code to retrieve and parse data from Enhetsregisteret"""
#!/usr/bin/python3

from os.path import exists
from xlsx2csv import Xlsx2csv
import pandas as pd
import numpy as np
import requests


OUTFILE = 'out.csv'

file_exists = exists(OUTFILE)

if file_exists == True:
         print("File exists")
else: 
        print("no exist")



def get_dataset():
        # Laster ned xlsx-fil med alle enheter i enhetsregisteret
        url = 'https://data.brreg.no/enhetsregisteret/api/enheter/lastned/regneark'
        headers = {'Accept': 'application/vnd.brreg.enhetsregisteret.enhet+vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=UTF-8'}
        session = requests.Session() # establish a session that is kept open during the transfer, instead of performing separate requests
        r = session.get(url, headers=headers, stream = True)
        r.raise_for_status()

        with open('er.xlsx','wb') as f:
                for chunk in r.iter_content(1024*1024*2): # laster ned og skriver ca 2 MB av gangen
                        f.write(chunk)

# Konverterer til CSV        
Xlsx2csv("er.xlsx", outputencoding="utf-8").convert("er.csv")

# Lager pandas dataframe 
df = pd.read_csv('er.csv', dtype={
        'Organisasjonsnummer': str,
        'Navn': str,
        'Organisasjonsform.kode': 'category',
        'Organisasjonsform.beskrivelse': 'category',
        'Næringskode 1': str,
        'Næringskode 1.beskrivelse': str,
        'Næringskode 2': str,
        'Næringskode 2.beskrivelse': str,
        'Næringskode 3': str,
        'Næringskode 3.beskrivelse': str,
        'Hjelpeenhetskode': 'category',
        'Hjelpeenhetskode.beskrivelse': 'category',
        'Antall ansatte': np.int16,
        'Hjemmeside': str,
        'Postadresse.adresse': str,
        'Postadresse.poststed': str,
        'Postadresse.postnummer': str,
        'Postadresse.kommune': str,
        'Postadresse.kommunenummer': str,
        'Postadresse.land': 'category',
        'Postadresse.landkode': 'category',
        'Forretningsadresse.adresse': str,
        'Forretningsadresse.poststed': str,
        'Forretningsadresse.postnummer': str,
        'Forretningsadresse.kommune': str,
        'Forretningsadresse.kommunenummer': str,
        'Forretningsadresse.land': 'category',
        'Forretningsadresse.landkode': 'category',
        'Institusjonell sektorkode': 'category',
        'Institusjonell sektorkode.beskrivelse': 'category',
        'Siste innsendte årsregnskap': str, # klarte ikke konvertere til np.int16
        'Registreringsdato i Enhetsregisteret': str, # klarer ikke konvertere 'datetime64',
        'Stiftelsesdato': str, # klarte ikke å konvertere til datetime64 - 1550-12-31 00:00:00
        'FrivilligRegistrertIMvaregisteret': 'category',
        'Registrert i MVA-registeret': 'category',
        'Registrert i Frivillighetsregisteret': 'category',
        'Registrert i Foretaksregisteret': 'category',
        'Registrert i Stiftelsesregisteret': 'category',
        'Konkurs': 'category',
        'Under avvikling': 'category',
        'Under tvangsavvikling eller tvangsoppløsning': 'category',
        'Overordnet enhet i offentlig sektor': str,
        'Målform': 'category' })

# Henter ut relevante kolonner
df2 = df[["Organisasjonsnummer", "Navn", 'Organisasjonsform.kode', "Organisasjonsform.beskrivelse", "Næringskode 1", "Næringskode 1.beskrivelse", "Postadresse.adresse", "Postadresse.kommune", "Registreringsdato i Enhetsregisteret", "Registrert i MVA-registeret"]]

# Konverterer datatype i alle kolonner til string
df3 = df2.astype(str)

# Liste med næringskoder for å sortere
searchfor = ["86.107","86.101","87.200"]

# Dataframe med filtrering på næringskoder i liste
enheter = df3[df3['Næringskode 1'].str.contains('|'.join(searchfor))]

#Skriver ut CSV
enheter.to_csv(OUTFILE) 
