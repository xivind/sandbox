#!/usr/bin/env python3

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    chroma_db_path: str = "./chroma_db"
    collection_name: str = "reguleringsplan_cleaned"  # Update this to match your collection
    model_name: str = "gpt-4o-mini-2024-07-18"
    chunk_size: int = 512
    chunk_overlap: int = 50
    max_tokens: int = 2000
    temperature: float = 0.7
    top_k: int = 4  # Number of most relevant chunks to use

    class Config:
        env_file = ".env"

def get_settings():
    return Settings()
