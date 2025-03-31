#!/usr/bin/env python3

import pandas as pd
import numpy as np
from typing import Dict, List
import re

def clean_and_enhance_csv(input_path: str, output_path: str):
    """
    Clean and enhance the reguleringsplan CSV file
    """
    # Read CSV
    df = pd.read_csv(input_path, encoding='latin-1')
    
    # 1. Text Cleaning
    text_columns = ['informasjonstype', 'navn', 'ingress', 'beskrivelse', 
                    'kontekstavhengig_beskrivelse', 'normeringsniva', 'eif_niva', 
                    'status', 'samhandlingstjenester', 'ansvarlig', 'dokumenttype',
                    'referanse_lenketekst', 'referanse_url']
    
    for col in text_columns:
        if col in df.columns:
            # Remove extra whitespace
            df[col] = df[col].astype(str).str.strip()
            
            # Standardize empty values
            df[col] = df[col].replace(['nan', 'None', ''], np.nan)
            
            # Clean text content
            df[col] = df[col].apply(lambda x: clean_text(x) if pd.notnull(x) else x)
    
    # 2. Create Combined Search Text
    df['search_text'] = df.apply(create_search_text, axis=1)
    
    # 3. Add Metadata Fields
    df['has_url'] = df['referanse_url'].notna()
    df['content_type'] = df.apply(determine_content_type, axis=1)
    
    # 4. Enhance Categorical Fields
    if 'normeringsniva' in df.columns:
        df['normeringsniva'] = df['normeringsniva'].fillna('ikke spesifisert')
        df['normeringsniva'] = df['normeringsniva'].str.lower()
    
    if 'status' in df.columns:
        df['status'] = df['status'].fillna('ikke spesifisert')
        df['status'] = df['status'].str.lower()
    
    # 5. Create Keywords Field
    df['keywords'] = df.apply(extract_keywords, axis=1)
    
    # 6. Handle URLs
    if 'referanse_url' in df.columns:
        df['referanse_url'] = df['referanse_url'].apply(clean_url)
    
    # Save enhanced CSV
    df.to_csv(output_path, index=False, encoding='utf-8')
    
    return df

def clean_text(text: str) -> str:
    """Clean and standardize text content"""
    if pd.isna(text):
        return text
        
    # Convert to string if not already
    text = str(text)
    
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep Norwegian characters
    text = re.sub(r'[^\w\s\-æøåÆØÅ.,()]', '', text)
    
    # Fix common abbreviations
    abbreviations = {
        'f.eks.': 'for eksempel',
        'bl.a.': 'blant annet',
        'evt.': 'eventuelt',
        'osv.': 'og så videre',
        'mv.': 'med videre'
    }
    for abbr, full in abbreviations.items():
        text = text.replace(abbr, full)
    
    return text.strip()

def create_search_text(row: pd.Series) -> str:
    """Create a combined searchable text field"""
    text_fields = ['informasjonstype', 'navn', 'ingress', 'beskrivelse', 
                   'kontekstavhengig_beskrivelse']
    
    # Combine all text fields with appropriate weights
    texts = []
    for field in text_fields:
        if field in row and pd.notnull(row[field]):
            if field in ['navn', 'informasjonstype']:
                # Repeat important fields to give them more weight
                texts.extend([str(row[field])] * 3)
            else:
                texts.append(str(row[field]))
    
    return ' '.join(texts)

def determine_content_type(row: pd.Series) -> str:
    """Determine the primary content type of the entry"""
    if pd.notnull(row.get('informasjonstype')):
        info_type = str(row['informasjonstype']).lower()
        if 'krav' in info_type:
            return 'krav'
        elif 'veileder' in info_type:
            return 'veileder'
        elif 'kodeverk' in info_type:
            return 'kodeverk'
    return 'annet'

def extract_keywords(row: pd.Series) -> str:
    """Extract key terms and phrases as keywords"""
    if pd.isna(row['beskrivelse']):
        return ''
        
    text = str(row['beskrivelse'])
    
    # Common important terms in the domain
    key_terms = ['krav', 'standard', 'veileder', 'forskrift', 'lov', 
                 'retningslinje', 'kodeverk', 'terminologi', 'api', 
                 'grensesnitt', 'samhandling', 'sikkerhet', 'personvern']
    
    # Extract matching terms
    found_terms = []
    for term in key_terms:
        if term in text.lower():
            found_terms.append(term)
    
    return ','.join(found_terms)

def clean_url(url: str) -> str:
    """Clean and validate URLs"""
    if pd.isna(url):
        return url
        
    url = str(url).strip()
    
    # Ensure URLs start with http:// or https://
    if url and not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    return url

if __name__ == "__main__":
    input_file = "raw_data/regulation-reports.csv"
    output_file = "raw_data/reguleringsplan_enhanced.csv"
    
    df = clean_and_enhance_csv(input_file, output_file)
    print("CSV enhancement completed successfully!")