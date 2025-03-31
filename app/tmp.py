#!/usr/bin/env python3

from typing import AsyncGenerator
import chromadb
from openai import AsyncOpenAI
import tiktoken
import asyncio
from icecream import ic
from dotenv import load_dotenv
import json
from .utils import read_json_file

CONFIG = read_json_file('app/config.json')
SECRETS = read_json_file('secrets.json')

# Initialize OpenAI API client
client = AsyncOpenAI(api_key=SECRETS['openai_api_key'])

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path=CONFIG['chroma_db_path'])
collection = chroma_client.get_collection(CONFIG['collection_name'])

THREAD_ID = None
ASSISTANT_ID = None

async def get_relevant_context(query: str) -> str:
    """
    Retrieve relevant context from the vector database for each query.
    Returns concatenated relevant documents.
    """
    # Get embeddings for the query
    response = await client.embeddings.create(
        model=CONFIG['embedding_model_name'],
        input=query)
    
    query_embedding = response.data[0].embedding

    # Query ChromaDB for relevant documents
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=CONFIG['top_k'])

    # Combine relevant chunks with clear separation
    contexts = results['documents'][0]
    return "\n\n---\n\n".join(contexts)

async def create_assistant():
    """Creates or retrieves an existing assistant."""
    global ASSISTANT_ID
    
    if ASSISTANT_ID:
        return ASSISTANT_ID

    assistant = await client.beta.assistants.create(
        name="Digitaliseringsekspert i helse- og omsorgssektoren",
        instructions="""Du er en ekspert på digitalisering innen helse- og omsorgssektoren i Norge. 
        Baser svarene dine primært på konteksten som gis.
        
        Svar skal være fullstendige og inkludere relevante lover, forskrifter og fortolkninger.""",
        model="gpt-4o-mini-2024-07-18"
    )
    ASSISTANT_ID = assistant.id
    return ASSISTANT_ID

async def generate_response(query: str, context: str) -> AsyncGenerator[str, None]:
    """
    Generate a streaming response using the OpenAI API.
    Now includes context with every query for better continuity and relevance.
    """
    try:
        global THREAD_ID
        
        # Create thread if it doesn't exist
        if not THREAD_ID:
            thread = await client.beta.threads.create()
            THREAD_ID = thread.id

        # Always combine context with query for better responses
        enriched_query = f"Context:\n{context}\n\nQuestion: {query}"
        
        # Create the message in the thread
        await client.beta.threads.messages.create(
            thread_id=THREAD_ID,
            role="user",
            content=enriched_query
        )
        
        # Get the assistant ID
        assistant_id = await create_assistant()
        
        async with client.beta.threads.runs.stream(
            thread_id=THREAD_ID,
            assistant_id=assistant_id,
            instructions="""
                    IMPORTANT ABOUT FORMATTING:
                    [HTML formatting instructions remain the same]
                    """
        ) as stream:
            async for chunk in stream:
                if chunk.event == "thread.message.delta":
                    if hasattr(chunk.data, 'delta') and chunk.data.delta:
                        if hasattr(chunk.data.delta, 'text'):
                            yield chunk.data.delta.text
                        elif hasattr(chunk.data.delta, 'content'):
                            for content_block in chunk.data.delta.content:
                                if content_block.type == 'text':
                                    yield content_block.text.value

    except Exception as e:
        error_message = f"Error in generate_response: {str(e)}"
        yield error_message

async def get_streaming_response(query: str) -> AsyncGenerator[str, None]:
    """
    Main function to handle the chat workflow.
    Now retrieves fresh context for every query.
    """
    # Get relevant context for each query
    context = await get_relevant_context(query)
    async for token in generate_response(query, context):
        yield token