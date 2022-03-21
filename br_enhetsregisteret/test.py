"""Code to retrieve and parse data from Enhetsregisteret"""
#!/usr/bin/python3

from lib2to3.pytree import convert
import os
from datetime import datetime
from os.path import exists
from xlsx2csv import Xlsx2csv
import pandas as pd
import numpy as np
import requests



FULLDATASET = 'er.xslx'

 
def prepare_full_dataset():
    url = 'https://data.brreg.no/enhetsregisteret/api/enheter/lastned/regneark'
    headers = {'Accept': 'application/vnd.brreg.enhetsregisteret.enhet+vnd.openxmlformats-officedocument.spreadsheetml.sheet;charset=UTF-8'}
    session = requests.Session() # establish a session that is kept open during the transfer, instead of performing separate requests
    r = session.get(url, headers=headers, stream = True)
    r.raise_for_status()

    print("Laster ned fullt datasett som .xslx")
    with open('er.xlsx','wb') as f:
        for chunk in r.iter_content(1024*1024*2): # laster ned og skriver ca 2 MB av gangen
            f.write(chunk)
    
    print("Konverterer fullt datasett til csv...")
    Xlsx2csv("er.xlsx", outputencoding="utf-8").convert("er.csv")
    
def prepare_dataframe():
    print("Gjør klar dataframe...")
    

def write_dataframe_to_csv():
    print("Skriver dataframe til csv...")
    

if exists(FULLDATASET) == True:
    print("Enhetsregisteret allerede lastet ned, versjon på disk:")
    print(f'Filnavn: {FULLDATASET} - Opprettet: {datetime.utcfromtimestamp(os.path.getctime(FULLDATASET)).strftime("%Y-%m-%d %H:%M:%S")}')
    user_input = input("Vil du laste ned på nytt (J/N): ")
    if user_input == "J":
        print("Laster ned fullt datasett på nytt")
        prepare_full_dataset()
    elif user_input == "N":
        print("Bruker eksisterende datasett")
    else:
        print("Vennligst følg anvisningene..")
        quit()

if exists(FULLDATASET) == False:
    print("Fant ikke fullt datasett...")
    prepare_full_dataset()

prepare_dataframe()

write_dataframe_to_csv()



