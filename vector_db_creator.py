#!/usr/bin/env python3

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import tiktoken
import openai
from openai import OpenAI
import chromadb
from tqdm import tqdm
import time
import logging
import os
from pathlib import Path
from app.utils import read_json_file


CONFIG = read_json_file('app/config.json')
SECRETS = read_json_file('secrets.json')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingPipeline:
    def __init__(self):

        self.client = OpenAI(api_key=SECRETS['openai_api_key'])
        self.model = CONFIG['embedding_model_name']
        self.chunk_size = CONFIG['chunk_size']
        self.chunk_overlap = CONFIG['chunk_overlap']
        self.batch_size = CONFIG['batch_size']
        self.max_retries = 3
        self.retry_delay = 1
        self.tokenizer = tiktoken.encoding_for_model(self.model)
        
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string."""
        return len(self.tokenizer.encode(text))
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap."""
        tokens = self.tokenizer.encode(text)
        chunks = []
        
        i = 0
        while i < len(tokens):
            # Get chunk_size tokens
            chunk_tokens = tokens[i:i + self.chunk_size]
            # Decode back to text
            chunk = self.tokenizer.decode(chunk_tokens)
            chunks.append(chunk)
            # Move forward by chunk_size - overlap
            i += (self.chunk_size - self.chunk_overlap)
            
        return chunks
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a batch of texts with retry logic."""
        embeddings = []
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            retry_count = 0
            
            while retry_count < self.max_retries:
                try:
                    response = self.client.embeddings.create(
                        model=self.model,
                        input=batch
                    )
                    batch_embeddings = [item.embedding for item in response.data]
                    embeddings.extend(batch_embeddings)
                    break
                    
                except Exception as e:
                    retry_count += 1
                    if retry_count == self.max_retries:
                        logger.error(f"Failed to get embeddings after {self.max_retries} retries: {str(e)}")
                        raise
                    logger.warning(f"Retry {retry_count}/{self.max_retries} after error: {str(e)}")
                    time.sleep(self.retry_delay * retry_count)
                    
        return embeddings
    
    def process_csv(self, csv_path: str, text_columns: List[str], encoding: str = None) -> Dict[str, Any]:
        """Process CSV file and generate embeddings for specified text columns."""
        logger.info(f"Processing CSV file: {csv_path}")
        
        # Try different encodings if none specified
        if encoding is None:
            encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
            for enc in encodings:
                try:
                    df = pd.read_csv(csv_path, encoding=enc)
                    logger.info(f"Successfully read CSV with {enc} encoding")
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.error(f"Error reading CSV with {enc} encoding: {str(e)}")
                    continue
            else:
                raise ValueError(f"Could not read CSV with any of the attempted encodings: {encodings}")
        else:
            df = pd.read_csv(csv_path, encoding=encoding)
        
        results = []
        for idx, row in tqdm(df.iterrows(), total=len(df)):
            # Combine specified text columns
            combined_text = " ".join([str(row[col]) for col in text_columns])
            chunks = self.chunk_text(combined_text)
            
            # Store metadata for each chunk
            for chunk_idx, chunk in enumerate(chunks):
                results.append({
                    'text': chunk,
                    'source_idx': idx,
                    'chunk_idx': chunk_idx,
                    'metadata': {col: row[col] for col in df.columns}
                })
        
        # Get embeddings for all chunks
        texts = [item['text'] for item in results]
        embeddings = self.get_embeddings(texts)
        
        # Add embeddings to results
        for idx, item in enumerate(results):
            item['embedding'] = embeddings[idx]
            
        return results
    
    def process_text_files(self, directory: str) -> Dict[str, Any]:
        """Process all text files in a directory."""
        logger.info(f"Processing text files in directory: {directory}")
        results = []
        
        for file_path in Path(directory).glob('*.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
                
            chunks = self.chunk_text(text)
            
            # Store metadata for each chunk
            for chunk_idx, chunk in enumerate(chunks):
                results.append({
                    'text': chunk,
                    'source': str(file_path),
                    'chunk_idx': chunk_idx
                })
        
        # Get embeddings for all chunks
        texts = [item['text'] for item in results]
        embeddings = self.get_embeddings(texts)
        
        # Add embeddings to results
        for idx, item in enumerate(results):
            item['embedding'] = embeddings[idx]
            
        return results
    
    def save_to_chromadb(self, data: List[Dict[str, Any]], collection_name: str, persist_directory: str = "./chroma_db"):
        """
        Save embeddings and metadata to ChromaDB.
        
        Args:
            data: List of documents with embeddings and metadata
            collection_name: Name of the collection to create
            persist_directory: Directory where ChromaDB will store its data
        """
        # Convert to absolute path and create directory if it doesn't exist
        persist_directory = os.path.abspath(persist_directory)
        os.makedirs(persist_directory, exist_ok=True)
        
        logger.info(f"ChromaDB data will be stored in: {persist_directory}")
        
        # Initialize ChromaDB with persistent storage
        client = chromadb.PersistentClient(path=persist_directory)
        
        # Delete collection if it already exists
        try:
            client.delete_collection(collection_name)
        except:
            pass
            
        collection = client.create_collection(name=collection_name)
        
        # Prepare data for ChromaDB
        ids = [f"doc_{i}" for i in range(len(data))]
        embeddings = [item['embedding'] for item in data]
        documents = [item['text'] for item in data]
        
        # Prepare metadata with guaranteed non-empty values
        metadatas = []
        for i, item in enumerate(data):
            # Start with basic metadata that we always have
            metadata = {'chunk_index': str(i),
                        'document_type': 'text'}
            
            # Add source information if available
            if 'source' in item:
                metadata['source'] = str(item['source'])
            if 'source_idx' in item:
                metadata['source_idx'] = str(item['source_idx'])
            if 'chunk_idx' in item:
                metadata['chunk_idx'] = str(item['chunk_idx'])
                
            # Add any additional metadata from the item
            if 'metadata' in item and isinstance(item['metadata'], dict):
                for k, v in item['metadata'].items():
                    metadata[k] = str(v)
                    
            metadatas.append(metadata)
            
        # Add to collection
        collection.add(ids=ids,
                       embeddings=embeddings,
                       documents=documents,
                       metadatas=metadatas)
        
        logger.info(f"Saved {len(data)} documents to ChromaDB collection '{collection_name}' with metadata")
        
        logger.info(f"Saved {len(data)} documents to ChromaDB collection '{collection_name}'")

if __name__ == "__main__":
    # Initialize the pipeline
    pipeline = EmbeddingPipeline()
    
    # Process CSV data
    csv_results = pipeline.process_csv(
        csv_path="raw_data/reguleringsplan_cleaned.csv",
        text_columns=['informasjonstype',
                      'navn',
                      'ingress',
                      'beskrivelse',
                      'kontekstavhengig_beskrivelse',
                      'normeringsniva',
                      'eif_niva',
                      'status',
                      'samhandlingstjenester',
                      'ansvarlig',
                      'dokumenttype',
                      'referanse_lenketekst',
                      'referanse_url'],
        encoding='latin-1'                      
    )
    
    # Process text files
    #text_results = pipeline.process_text_files(directory="./raw_data")
    
    # Combine results
    #all_results = csv_results + text_results
    
    # Save to ChromaDB
    pipeline.save_to_chromadb(csv_results, "reguleringsplan_cleaned")