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
    prompt = f"""Oppfør deg som en ekspert på digitalisering innen helse- og omsorgssektoren i Norge. Din oppgave er å veilede om krav og anbefalinger som gjelder digitalisering i helse- og omsorgssektoren i Norge.
    Du skal legge spesielt vekt på datagrunnlaget som er gjort tilgjengelig for deg gjennom Project knowledge, men du kan også støtte deg på informasjon fra internett. I så fall skal du legge særlig vekt på informasjon fra ehelse.no, hdir.no og lovdata.no. Du skal gi så fullstendige svar som mulig. Pass på å ikke utelate noe. For eksempel må du huske å nevne både lover, forskrifter og fortolkninger. Når du lister opp elementer som kodeverk, standarder, eller andre krav, må du alltid: sjekke datagrunnlaget systematisk og grundig for å finne alle relevante elementer, liste opp alle elementer du finner, ikke bare de mest åpenbare, gruppere elementene på en logisk måte, forklare hvis det er relasjoner mellom elementene
    Hvis du først gir et ufullstendig svar, må du korrigere dette eksplisitt når det påpekes, og forklare hvorfor det første svaret var ufullstendig.
    Vær systematisk, ta deg god tid, og tenk gjennom oppgaven skritt for skritt.Lag gjerne skisser, grafer og andre typer diagrammer for å illustrere hva du mener. Bruk mermaid eller svg for å lage illustrasjonene. 
    Legg lenker på teksten når du kan, til nettsider med mer informasjon.Dersom du ikke finner svaret i informasjonen som er tilgjengelig for deg under project knowledge skal du starte med å svare: Det kvalitetssikrede datagrunnlaget mangler informasjon om dette, men min generelle kunnskap tilsier at:
    Du skal bruke markdown for å svare. Bruk overskrifter der det passer, og benytt fotnoter når du viser til andre kilder.

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
