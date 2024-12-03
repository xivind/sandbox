#!/usr/bin/env python3

from typing import AsyncGenerator
import chromadb
from openai import AsyncOpenAI
import asyncio
from .utils import read_json_file

CONFIG = read_json_file('app/config.json')
SECRETS = read_json_file('secrets.json')

client = AsyncOpenAI(api_key=SECRETS['openai_api_key'])
chroma_client = chromadb.PersistentClient(path=CONFIG['chroma_db_path'])
collection = chroma_client.get_collection(CONFIG['collection_name'])

THREAD_ID = None
ASSISTANT_ID = None
IS_FIRST_MESSAGE = True

async def get_relevant_context(query: str) -> str:
    response = await client.embeddings.create(
        model=CONFIG['embedding_model_name'],
        input=query)
    
    query_embedding = response.data[0].embedding
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=CONFIG['top_k'])
    
    return "\n\n---\n\n".join(results['documents'][0])

async def ensure_assistant():
    global ASSISTANT_ID
    if ASSISTANT_ID:
        return ASSISTANT_ID

    assistant = await client.beta.assistants.create(
        name="Health Sector Digitalization Expert",
        instructions="""Du er en ekspert på digitalisering innen helse- og omsorgssektoren i Norge. 
        Baser svarene dine primært på konteksten som gis.
        
        Format svarene med HTML-tags:
        - <h1> for hovedoverskrift
        - <h2> for underoverskrifter
        - <p> for tekstavsnitt
        - <ul>/<li> for punktlister
        - <ol>/<li> for nummererte lister
        - <a href="url"> for lenker
        - <strong> for uthevet tekst
        - <br> for linjeskift
        
        Svar skal være fullstendige og inkludere relevante lover, forskrifter og fortolkninger.""",
        model="gpt-4o-mini-2024-07-18"
    )
    ASSISTANT_ID = assistant.id
    return ASSISTANT_ID

async def get_streaming_response(query: str) -> AsyncGenerator[str, None]:
    try:
        global THREAD_ID, IS_FIRST_MESSAGE
        
        if not THREAD_ID:
            thread = await client.beta.threads.create()
            THREAD_ID = thread.id
            IS_FIRST_MESSAGE = True
        
        # Only get full context for first message
        content = query
        if IS_FIRST_MESSAGE:
            context = await get_relevant_context(query)
            content = f"Context:\n{context}\n\nQuestion: {query}"
            IS_FIRST_MESSAGE = False
        
        await client.beta.threads.messages.create(
            thread_id=THREAD_ID,
            role="user",
            content=content
        )
        
        assistant_id = await ensure_assistant()
        run = await client.beta.threads.runs.create(
            thread_id=THREAD_ID,
            assistant_id=assistant_id
        )
        
        while True:
            run_status = await client.beta.threads.runs.retrieve(
                thread_id=THREAD_ID,
                run_id=run.id
            )
            
            if run_status.status == 'completed':
                messages = await client.beta.threads.messages.list(
                    thread_id=THREAD_ID
                )
                latest_message = messages.data[0]
                if latest_message.role == "assistant":
                    text = latest_message.content[0].text.value
                    for char in text:
                        yield char
                break
            elif run_status.status in ['failed', 'cancelled', 'expired']:
                print(f"Run failed with status: {run_status.status}")
                print(f"Run details: {run_status}")
                THREAD_ID = None
                IS_FIRST_MESSAGE = True
                yield f"Error: Assistant run {run_status.status}. Please try again."
                break
                
            await asyncio.sleep(0.5)
            
    except Exception as e:
        print(f"Error in get_streaming_response: {str(e)}")
        yield f"Error: {str(e)}"