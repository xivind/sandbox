"""Code to retrieve and parse data from Enhetsregisteret"""
#!/usr/bin/python3

import os
from datetime import datetime
from os.path import exists
from xlsx2csv import Xlsx2csv
import pandas as pd
import numpy as np
import requests
from icecream import ic


#DEUBG = YES
OUTFILE = "out.csv"
FULLDATASET = "er.xlsx"
NACE_CODES = "86.101, 86.102, 86.103, 86.104"
#NACE_CODES = "86.1, 86.10, 86.101, 86.102, 86.103, 86.104, 86.105, 86.106, 86.107, 86.2, 86.21, 86.211, 86.212, 86.22, 86.221, 86.222, 86.223, 86.224, 86.225, 86.23, 86.230, 86.9, 86.90, 86.901, 86.902, 86.903, 86.904, 86.905, 86.906, 86.907, 87, 87.1, 87.10, 87.101, 87.102, 87.2, 87.20, 87.201, 87.202, 87.203, 87.3, 87.30, 87.301, 87.302, 87.303, 87.304, 87.305, 87.9, 87.90, 87.901, 87.909"

def get_overview():
    ic()
    datainfo = requests.get(f'https://data.brreg.no/enhetsregisteret/api/enheter?naeringskode={NACE_CODES}&page=0', headers=requests.utils.default_headers()).json()
    print(f'Treff på for næringskode(r) {NACE_CODES}:')
    print(f'Totalt antall elementer: {datainfo.get("page").get("totalElements")}, totalt antall sider: {datainfo.get("page").get("totalPages")}')


def prepare_full_dataset():
    url = 'https://data.brreg.no/enhetsregisteret/api/enheter/lastned/regneark'
    headers = {'Accept': 'application/vnd.brreg.enhetsregisteret.enhet+vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=UTF-8'}
    session = requests.Session() # establish a session that is kept open during the transfer, instead of performing separate requests
    r = session.get(url, headers=headers, stream = True)
    r.raise_for_status()

    print("Laster ned fullt datasett som .xslx")
    with open("er.xlsx","wb") as f:
        for chunk in r.iter_content(1024*1024*2): # laster ned og skriver ca 2 MB av gangen
            f.write(chunk)
    
    print("Konverterer fullt datasett til csv...")
    Xlsx2csv("er.xlsx", outputencoding="utf-8").convert("er.csv")
    
def prepare_dataframe():
    print("Gjør klar dataframe...")

    df = pd.read_csv("er.csv", dtype={
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
    df2 = df[["Organisasjonsnummer", "Navn", 'Organisasjonsform.kode', "Organisasjonsform.beskrivelse", "Næringskode 1", "Næringskode 1.beskrivelse", "Næringskode 2", "Næringskode 3", "Postadresse.adresse", "Postadresse.kommune", "Registreringsdato i Enhetsregisteret"]]

    # Konverterer datatype i alle kolonner til string
    df3 = df2.astype(str)

    # Liste med næringskoder for å sortere
    searchfor = ["86.101", "86.102", "86.103", "86.104"]

    # Dataframe med filtrering på næringskoder i liste
    nkode1 = df3[df3['Næringskode 1'].str.contains('|'.join(searchfor))]
    nkode2 = df3[df3['Næringskode 2'].str.contains('|'.join(searchfor))]
    nkode3 = df3[df3['Næringskode 3'].str.contains('|'.join(searchfor))]
    
    ic(nkode1)
    ic(nkode2)
    ic(nkode3)
    
    # Use pandas.concat() method to ignore_index 
    enheter = pd.concat([nkode1, nkode2, nkode3], ignore_index=True, sort=False)
    
    ic()
    ic(enheter)
    return enheter
    

def write_dataframe_to_csv(dump):
    print("Skriver dataframe til csv...")
    dump.to_csv(OUTFILE) 

#Program starts here    
get_overview()
user_input = input("Vil du lagre spørringens innhold? (J/N): ")
if user_input == "J":
    if exists(FULLDATASET) == True:
        print("Enhetsregisteret allerede lastet ned, versjon på disk:")
        print(f'Filnavn: {FULLDATASET} - Opprettet: {datetime.utcfromtimestamp(os.path.getctime(FULLDATASET)).strftime("%Y-%m-%d %H:%M:%S")}')
        user_input = input("Vil du laste ned på nytt? (J/N): ")
        if user_input == "J":
            print("Laster ned fullt datasett på nytt")
            prepare_full_dataset()
        elif user_input == "N":
            print("Bruker eksisterende datasett")
        else:
            print("Vennligst følg anvisningene..")
            quit()

    if exists(FULLDATASET) == False:
        print("Fant ikke fullt datasett")
        prepare_full_dataset()

    data = prepare_dataframe()

    write_dataframe_to_csv(data)

elif user_input == "N":
    print("Program stoppet")
else:
    print("Vennligst følg anvisningene..")
    quit()
