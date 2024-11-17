#!/usr/bin/env python3

import pandas as pd  
import nltk  
import re  
from nltk.stem import PorterStemmer  
from nltk.stem import WordNetLemmatizer  
from nltk.corpus import stopwords  
 
# Load the CSV file  
df = pd.read_csv('download-regulation-reports.csv', encoding='latin-1')    
 
# Download NLTK data files (only need to run once)  
nltk.download('wordnet')  
nltk.download('stopwords')  
 
# Initialize stemmer and lemmatizer  
stemmer = PorterStemmer()  
lemmatizer = WordNetLemmatizer()  
stop_words = set(stopwords.words('norwegian'))  # Assuming Norwegian stopwords based on the dataset language  
 
# Remove duplicate entries  
df = df.drop_duplicates()  
 
# Handle missing values: fill missing values with an empty string  
df = df.fillna('')  
 
# Ensure consistent formatting: strip leading/trailing spaces and convert to lower case  
df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)  
df = df.applymap(lambda x: x.lower() if isinstance(x, str) else x)  
 
# Remove special characters except for Norwegian characters  
def remove_special_characters(text):  
    text = re.sub(r'[^a-zA-Z0-9æøåÆØÅ\s]', '', text)  
    return text  
 
# Remove stop words  
def remove_stopwords(text):  
    words = text.split()  
    filtered_words = [word for word in words if word not in stop_words]  
    return ' '.join(filtered_words)  
 
# Example function to apply stemming and lemmatization  
def stem_and_lemmatize(text):  
    words = text.split()  
    stemmed_words = [stemmer.stem(word) for word in words]  
    lemmatized_words = [lemmatizer.lemmatize(word) for word in stemmed_words]  
    return ' '.join(lemmatized_words)  
 
# Apply cleaning steps to text columns  
# Don't make changes to 'referanse_url'
text_columns = ['navn', 'ingress', 'beskrivelse', 'kontekstavhengig_beskrivelse', 'samhandlingstjenester', 'ansvarlig', 'dokumenttype', 'referanse_lenketekst']  
for column in text_columns:  
    df[column] = df[column].apply(remove_special_characters)  
    df[column] = df[column].apply(remove_stopwords)  
    # df[column] = df[column].apply(stem_and_lemmatize)  
 
# Remove unnecessary columns: list columns to keep  
columns_to_keep = [  
    'informasjonstype', 'navn', 'ingress', 'beskrivelse',  
    'kontekstavhengig_beskrivelse', 'normeringsniva', 'eif_niva',  
    'status', 'samhandlingstjenester', 'ansvarlig', 'dokumenttype',  
    'referanse_lenketekst', 'referanse_url'  
]  
 
# Keep only the necessary columns  
df = df[columns_to_keep]  
 
# Save the cleaned data to a new CSV file with UTF-8 encoding  
df.to_csv('reguleringsplan_cleaned.csv', index=False, encoding='utf-8')  
 
print("Data cleaning completed and saved to file")