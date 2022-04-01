"""Code to retrieve data from Enhetsregisteret and prepare CSV for ingest"""
#!/usr/bin/python3

from multiprocessing.spawn import prepare
import os
from datetime import datetime
from os.path import exists
from xlsx2csv import Xlsx2csv
import pandas as pd
import numpy as np
import requests
from icecream import ic

#DEUBG = YES
NACE_UTVALG = "86.1, 86.2, 86.9, 87.1, 87.2, 87.3, 87.9, 88.1, 88.9"
NACE_SOK = "86.101, 86.102, 86.103, 86.104"
ER_UTVALG = "er_subset.csv"
ER_SOKERESULTAT = "er_search_result.csv"


def get_overview():
    ic()
    datainfo = requests.get(f'https://data.brreg.no/enhetsregisteret/api/enheter?naeringskode={NACE_CODES}&page=0', headers=requests.utils.default_headers()).json()
    print(f'Treff på for næringskode(r) {NACE_CODES}:')
    print(f'Totalt antall elementer: {datainfo.get("page").get("totalElements")}, totalt antall sider: {datainfo.get("page").get("totalPages")}')

def download_er():
    url = 'https://data.brreg.no/enhetsregisteret/api/enheter/lastned/regneark'
    headers = {'Accept': 'application/vnd.brreg.enhetsregisteret.enhet+vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=UTF-8'}
    session = requests.Session() # establish a session that is kept open during the transfer, instead of performing separate requests
    r = session.get(url, headers=headers, stream = True)
    r.raise_for_status()

    print("Laster ned fullt datasett som .xlsx")
    with open("er.xlsx","wb") as f:
        for chunk in r.iter_content(1024*1024*2): # laster ned og skriver ca 2 MB av gangen
            f.write(chunk)
    
def prepare_subset():
    print("Konverterer fullt datasett til csv...")
    Xlsx2csv("er.xlsx", outputencoding="utf-8").convert("er1.csv", sheetid=1)
    Xlsx2csv("er.xlsx", outputencoding="utf-8").convert("er2.csv", sheetid=2)

    print("Gjør klar dataframe...")
    df1 = pd.read_csv('er1.csv')
     
    df2 = pd.read_csv('er2.csv')
    
    # Use pandas.concat() method to get one dataframe from both sheets 
    df = pd.concat([df1, df2], ignore_index=True, sort=False)
   
    # Henter ut relevante kolonner
    df2 = df[["Organisasjonsnummer", "Navn", 'Organisasjonsform.kode', "Organisasjonsform.beskrivelse", "Næringskode 1", "Næringskode 1.beskrivelse", "Næringskode 2", "Næringskode 3", "Postadresse.adresse", "Postadresse.kommune", "Registreringsdato i Enhetsregisteret"]]
    # Konverterer datatype i alle kolonner til string
    df3 = df2.astype(str)

    # Liste med næringskoder for å sortere
    searchfor = ["86.1", "86.2", "86.9", "87.1", "87.2", "87.3", "87.9", "88.1", "88.9"]
    #searchfor = ["86.101", "86.102", "86.103", "86.104"]

    # Dataframe med filtrering på næringskoder i liste
    nkode1 = df3[df3['Næringskode 1'].str.contains('|'.join(searchfor))]
    nkode2 = df3[df3['Næringskode 2'].str.contains('|'.join(searchfor))]
    nkode3 = df3[df3['Næringskode 3'].str.contains('|'.join(searchfor))]
    
    ic(nkode1)
    ic(nkode2)
    ic(nkode3)
    
    # Use pandas.concat() method to ignore_index 
    utvalg = pd.concat([nkode1, nkode2, nkode3], ignore_index=True, sort=False).drop_duplicates(subset=['Organisasjonsnummer'])
    
    ic()
    ic(utvalg)
    return utvalg

def prepare_search_result():
    pass
    
def prepare_dataframe():
    
    

def write_dataframe_to_csv(dump):
    print("Skriver dataframe til csv...")
    dump.to_csv(OUTFILE) 

def show_stats():
    pass

def show_data():
    pass

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

#hvorfor er det avvik?