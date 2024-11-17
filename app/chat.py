#!/usr/bin/env python3

from typing import AsyncGenerator
import chromadb
from openai import AsyncOpenAI
import tiktoken
from .config import get_settings
from icecream import ic


settings = get_settings() #This causes a caching problem
client = AsyncOpenAI(api_key=settings.openai_api_key)

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path=settings.chroma_db_path)
collection = chroma_client.get_collection("reguleringsplan_cleaned")

async def get_relevant_context(query: str) -> str:
    """
    Retrieve relevant context from the vector database
    """
    # Get embeddings for the query
    response = await client.embeddings.create(
        model="text-embedding-3-large",
        input=query)
    
    query_embedding = response.data[0].embedding

    # Query ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=settings.top_k)

    # Combine relevant chunks
    contexts = results['documents'][0]
    print(len(contexts))
    for item in contexts:
        print("New item")
        print(f"{item} \n")
    return "\n\n---\n\n".join(contexts)

async def generate_response(query: str, context: str) -> AsyncGenerator[str, None]:
    """
    Generate a streaming response using the OpenAI API
    """
    prompt = f"""Oppfør deg som en ekspert på digitalisering innen helse- og omsorgssektoren i Norge.
    Din oppgave er å veilede om krav og anbefalinger som gjelder digitalisering i helse- og omsorgssektoren i Norge.
    Du skal legge spesielt vekt på datagrunnlaget som inngår i denne prompten, men du kan også støtte deg på informasjon fra internett.
    I så fall skal du legge særlig vekt på informasjon fra ehelse.no, hdir.no og lovdata.no. Du skal gi så fullstendige svar som mulig.
    Pass på å ikke utelate noe. For eksempel må du huske å nevne både lover, forskrifter og fortolkninger. 

    Når du lister opp elementer som kodeverk, standarder, eller andre krav, må du alltid: 
    - sjekke datagrunnlaget systematisk og grundig for å finne alle relevante elementer
    - liste opp alle elementer du finner, ikke bare de mest åpenbare
    - gruppere elementene på en logisk måte
    - forklare hvis det er relasjoner mellom elementene

    VIKTIG OM FORMATTERING:
    Du skal svare med HTML-formattering. Bruk følgende HTML-elementer:
    - <h1> for hovedoverskrift
    - <h2> for underoverskrifter
    - <p> for tekstavsnitt
    - <ul> og <li> for punktlister
    - <ol> og <li> for nummererte lister
    - <a href="url"> for lenker
    - <strong> for uthevet tekst
    - <br> for linjeskift der det trengs

    VIKTIG: 
    - IKKE start svaret med ```html
    - IKKE avslutt svaret med ``
    - Bruk komplette HTML-tags (<ul><li>punkt</li></ul>, ikke bare 'ul>')
    - IKKE skriv 'ul>' separat
    - IKKE skriv 'ol>' separat

    Eksempel på formattering:
    <h1>Hovedtittel</h1>
    <p>Et avsnitt med tekst som kan inneholde <strong>uthevet tekst</strong> og <a href="https://ehelse.no">lenker</a>.</p>
    <h2>Undertittel</h2>
    <ul>
        <li>Punkt 1</li>
        <li>Punkt 2</li>
    </ul>

    Context: {context}

    Question: {query}

    Answer:"""

    response = await client.chat.completions.create(
        model=settings.model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        stream=True)

    async for chunk in response:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content

async def get_streaming_response(query: str) -> AsyncGenerator[str, None]:
    """
    Main function to handle the chat workflow
    """
    context = await get_relevant_context(query)
    async for token in generate_response(query, context):
        yield token
