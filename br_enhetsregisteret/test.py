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
ER_FULL_FIL = "er.xlsx"
ER_UTVALG_FIL = "er_subset.csv"
ER_SOK_FIL = "er_search_result.csv"


def sjekk_api():
    ic()
    print("Spørring direkte mot API...")
    datainfo = requests.get(f'https://data.brreg.no/enhetsregisteret/api/enheter?naeringskode={NACE_SOK}&page=0', headers=requests.utils.default_headers()).json()
    print(f'Treff på for næringskode(r) {NACE_SOK}:')
    print(f'Totalt antall elementer: {datainfo.get("page").get("totalElements")}, totalt antall sider: {datainfo.get("page").get("totalPages")}')

def hent_er():
    ic()
    print("Laster ned fullt datasett som xlsx...")
    url = 'https://data.brreg.no/enhetsregisteret/api/enheter/lastned/regneark'
    headers = {'Accept': 'application/vnd.brreg.enhetsregisteret.enhet+vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=UTF-8'}
    session = requests.Session() # establish a session that is kept open during the transfer, instead of performing separate requests
    r = session.get(url, headers=headers, stream = True)
    r.raise_for_status()

    with open(ER_FULL_FIL,"wb") as f:
        for chunk in r.iter_content(1024*1024*2): # laster ned og skriver ca 2 MB av gangen
            f.write(chunk)

    lag_utvalg()

def skriv_csv(data, utfil):
    ic()
    print(f'Skriver dataframe til {utfil}...')
    data.to_csv(utfil)

def lag_utvalg():
    ic()
    print("Konverterer fane 1 av fullt datasett til csv...")
    Xlsx2csv("er.xlsx", outputencoding="utf-8").convert("er1.csv", sheetid=1)
    print("Konverterer fane 2 av fullt datasett til csv...")
    Xlsx2csv("er.xlsx", outputencoding="utf-8").convert("er2.csv", sheetid=2)

    print("Gjør klar utvalg...")
    df_fane1 = pd.read_csv('er1.csv')
    df_fane2 = pd.read_csv('er2.csv')
    df_kombinert = pd.concat([df_fane1, df_fane2], ignore_index=True, sort=False)
    df_kombinert_trimmet = df_kombinert[["Organisasjonsnummer", "Navn", 'Organisasjonsform.kode', "Organisasjonsform.beskrivelse", "Næringskode 1", "Næringskode 1.beskrivelse", "Næringskode 2", "Næringskode 2.beskrivelse", "Næringskode 3", "Næringskode 3.beskrivelse", "Postadresse.adresse", "Postadresse.kommune", "Registreringsdato i Enhetsregisteret"]]
    df_utvalg = df_kombinert_trimmet.astype(str)

    searchfor = ["86.1", "86.2", "86.9", "87.1", "87.2", "87.3", "87.9", "88.1", "88.9"] #Denne må endres til variabel
    
    nace_utvalg_1 = df_utvalg[df_utvalg['Næringskode 1'].str.contains('|'.join(searchfor))]
    nace_utvalg_2 = df_utvalg[df_utvalg['Næringskode 2'].str.contains('|'.join(searchfor))]
    nace_utvalg_3 = df_utvalg[df_utvalg['Næringskode 3'].str.contains('|'.join(searchfor))]
    
    ic(nace_utvalg_1)
    ic(nace_utvalg_2)
    ic(nace_utvalg_3)
    
    utvalg = pd.concat([nace_utvalg_1, nace_utvalg_2, nace_utvalg_3], ignore_index=True, sort=False).drop_duplicates(subset=['Organisasjonsnummer'])
    
    skriv_csv(utvalg, ER_UTVALG_FIL)

def lag_sokeresultat():
    ic()
    print("Gjør klar utvalg...")
    df_utvalg = pd.read_csv('ER_UTVALG_FIL')

    searchfor = ["86.1", "86.2", "86.9", "87.1", "87.2", "87.3", "87.9", "88.1", "88.9"] #Denne må endres til variabel

    nace_sok_1 = df_utvalg[df_utvalg['Næringskode 1'].str.contains('|'.join(searchfor))]
    nace_sok_2 = df_utvalg[df_utvalg['Næringskode 2'].str.contains('|'.join(searchfor))]
    nace_sok_3 = df_utvalg[df_utvalg['Næringskode 3'].str.contains('|'.join(searchfor))]

    sok = pd.concat([nace_sok_1, nace_sok_2, nace_sok_3], ignore_index=True, sort=False).drop_duplicates(subset=['Organisasjonsnummer'])

    ic(nace_sok_1)
    ic(nace_sok_2)
    ic(nace_sok_3)

    skriv_csv(sok, ER_SOK_FIL)

    return sok 

def vis_statistikk(data):
    ic()
    print("Viser statistikK...")
    print(data.groupby('Næringskode 1.beskrivelse')['Næringskode 1.beskrivelse'].count())
    print(data.groupby('Organisasjonsform.beskrivelse')['Organisasjonsform.beskrivelse'].count())
    pass

def vis_data(data):
    ic()
    print("Viser data...") #Mangler innhold...
    pass

#Program starts here
sjekk_api()
user_input = input("Lagre spørringens innhold? (J/N): ")
if user_input == "J":
    if exists(ER_FULL_FIL) == True:
        print(f'Bruker Enhetsregisteret lasted ned {datetime.utcfromtimestamp(os.path.getctime(ER_FULL_FIL)).strftime("%Y-%m-%d %H:%M:%S")}')
    
        if exists(ER_UTVALG_FIL) == True:
            user_input = input(f'Bruke eksisterende grovutvalg: {NACE_UTVALG} ? (lagd {datetime.utcfromtimestamp(os.path.getctime(ER_UTVALG_FIL)).strftime("%Y-%m-%d %H:%M:%S")}) (J/N)')
            if user_input == "N":
                lag_utvalg()
                resultat = lag_sokeresultat()
            
            elif user_input == "J":
                print("Bruker eksisterende grovutvalg..")
                resultat = lag_sokeresultat()
                        
            else:
                print("Vennligst følg anvisningene..")
                quit()
        
    if exists(ER_UTVALG_FIL) == False:
        lag_utvalg()
        resultat = lag_sokeresultat()

    user_input = input("Vise statistikk? (J/N): ")
    if user_input == "J":
        vis_statistikk(resultat)

    user_input = input("Vise data? (J/N): ")
    if user_input == "J":
        vis_data(resultat)


else:
    print("Program avsluttet")
    quit()