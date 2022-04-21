"""Kode for å hente underenheter fra Enhetsregisteret og gjøre klar CSV for analyse"""
#!/usr/bin/python3

import os
from datetime import datetime
from os.path import exists
from xlsx2csv import Xlsx2csv
import pandas as pd
import requests
from icecream import ic

#Debug av/på
ic.disable()

NACE_UTVALG = "86.1,86.2,86.9,87.1,87.2,87.3,87.9,88.1,88.9"
NACE_SOK = "86.101,86.103,87.201"
ER_FULL_FIL = "er_underenheter.xlsx"
ER_UTVALG_FIL = "er_underenheter_subset.csv"
ER_SOK_FIL = "er_underenheter_search_result.csv"


def sjekk_api():
    ic()
    print("Spørring direkte mot API...")
    datainfo = requests.get(f'https://data.brreg.no/enhetsregisteret/api/underenheter?naeringskode={NACE_SOK}&page=0', headers=requests.utils.default_headers()).json()
    print(f'Treff i API for næringskode(r) {NACE_SOK}:')
    print(f'Totalt antall elementer: {datainfo.get("page").get("totalElements")}, totalt antall sider: {datainfo.get("page").get("totalPages")}')

def hent_er():
    ic()
    print("Laster ned fullt datasett som xlsx...")
    url = 'https://data.brreg.no/enhetsregisteret/api/underenheter/lastned/regneark'
    headers = {'Accept': 'application/vnd.brreg.enhetsregisteret.underenhet+vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=UTF-8'}
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
    Xlsx2csv(ER_FULL_FIL, outputencoding="utf-8").convert("er_underenheter.csv", sheetid=1)

    print("Gjør klar utvalg...")
    df_fane1 = pd.read_csv('er_underenheter.csv')
    df_fane1_trimmet = df_fane1[["Overordnet Enhet", "Organisasjonsnummer", "Navn", 'Organisasjonsform.kode', "Organisasjonsform.beskrivelse", "Næringskode 1", "Næringskode 1.beskrivelse", "Næringskode 2", "Næringskode 2.beskrivelse", "Næringskode 3", "Næringskode 3.beskrivelse", "Postadresse.adresse", "Postadresse.kommune", "Registreringsdato i Enhetsregisteret", "Antall ansatte"]]
    df_utvalg = df_fane1_trimmet.astype(str)
 
    sok_etter = list(NACE_UTVALG.split(","))

    nace_utvalg_1 = df_utvalg[df_utvalg['Næringskode 1'].str.contains('|'.join(sok_etter))]
    nace_utvalg_2 = df_utvalg[df_utvalg['Næringskode 2'].str.contains('|'.join(sok_etter))]
    nace_utvalg_3 = df_utvalg[df_utvalg['Næringskode 3'].str.contains('|'.join(sok_etter))]
    
    ic(nace_utvalg_1)
    ic(nace_utvalg_2)
    ic(nace_utvalg_3)
    
    utvalg = pd.concat([nace_utvalg_1, nace_utvalg_2, nace_utvalg_3], ignore_index=True, sort=False).drop_duplicates(subset=['Organisasjonsnummer'])
    
    skriv_csv(utvalg, ER_UTVALG_FIL)

def lag_sokeresultat():
    ic()
    print("Gjør klar søkeresultat...")
    df_utvalg = pd.read_csv(ER_UTVALG_FIL)
    df_utvalg = df_utvalg.astype(str)
 
    sok_etter = list(NACE_SOK.split(","))

    nace_sok_1 = df_utvalg[df_utvalg['Næringskode 1'].str.contains('|'.join(sok_etter))]
    nace_sok_2 = df_utvalg[df_utvalg['Næringskode 2'].str.contains('|'.join(sok_etter))]
    nace_sok_3 = df_utvalg[df_utvalg['Næringskode 3'].str.contains('|'.join(sok_etter))]

    sok = pd.concat([nace_sok_1, nace_sok_2, nace_sok_3], ignore_index=True, sort=False).drop_duplicates(subset=['Organisasjonsnummer'])

    ic(nace_sok_1)
    ic(nace_sok_2)
    ic(nace_sok_3)

    skriv_csv(sok, ER_SOK_FIL)

    return sok 

def vis_statistikk(data):
    ic()
    print("Viser statistikk...")
    print(data.groupby('Næringskode 1.beskrivelse')['Næringskode 1.beskrivelse'].count())
    print(data.groupby('Organisasjonsform.beskrivelse')['Organisasjonsform.beskrivelse'].count())
    print(f'Antall enheter i søkeresultat CSV (sjekk mot tall fra API over): {len(data)}')
    
#Program starts here
sjekk_api()
if exists(ER_FULL_FIL) == True:
    print(f'Bruker Enhetsregisteret lasted ned {datetime.utcfromtimestamp(os.path.getctime(ER_FULL_FIL)).strftime("%Y-%m-%d %H:%M:%S")}')
    
    if exists(ER_UTVALG_FIL) == True:
        print(f'Bruker grovutvalg laget {datetime.utcfromtimestamp(os.path.getctime(ER_UTVALG_FIL)).strftime("%Y-%m-%d %H:%M:%S")}')
        resultat = lag_sokeresultat()
        vis_statistikk(resultat)
            
    if exists(ER_UTVALG_FIL) == False:
        print("Fant ikke utvalgsfil")
        lag_utvalg()
        resultat = lag_sokeresultat()
        vis_statistikk(resultat)
        
elif exists(ER_FULL_FIL) == False:
        hent_er()
        resultat = lag_sokeresultat()
        vis_statistikk(resultat)
