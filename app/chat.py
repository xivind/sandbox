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

async def get_relevant_context(query: str) -> str: #Check why this function is different from same function in assistant script
    """
    Retrieve relevant context from the vector database
    """
    # Get embeddings for the query
    response = await client.embeddings.create(
        model = CONFIG['embedding_model_name'],
        input = query)
    
    query_embedding = response.data[0].embedding

    # Query ChromaDB
    results = collection.query(
        query_embeddings = [query_embedding],
        n_results = CONFIG['top_k'])

    # Combine relevant chunks
    contexts = results['documents'][0]
    print(len(contexts))
    for item in contexts:
        print("New item")
        print(f"{item} \n")
    return "\n\n---\n\n".join(contexts)

async def create_assistant():
  global ASSISTANT_ID
  
  if ASSISTANT_ID:
    return ASSISTANT_ID

  #Replace assistant instruction with read from file
  assistant = await client.beta.assistants.create(
      name="Digitaliseringsekspert i helse- og omsorgssektoren",
      instructions="""Du er en ekspert på digitalisering innen helse- og omsorgssektoren i Norge. 
      Baser svarene dine primært på konteksten som gis.

      Svar skal være fullstendige og inkludere relevante lover, forskrifter og fortolkninger.""",
      model="gpt-4o-mini-2024-07-18" #Read from file instead
  )
  ASSISTANT_ID = assistant.id
  return ASSISTANT_ID

async def generate_response(query: str, context: str) -> AsyncGenerator[str, None]:
    """
    Generate a streaming response using the OpenAI API with added console logging
    for debugging purposes.
    """
    try:
        global THREAD_ID
        
        print("\nDebug: Starting generate_response function")
        
        # Create thread if it doesn't exist
        if not THREAD_ID:
            thread = await client.beta.threads.create()
            THREAD_ID = thread.id
            print(f"Debug: Created new thread with ID: {THREAD_ID}")
        else:
            print(f"Debug: Using existing thread with ID: {THREAD_ID}")
        
        # Always combine context with query for better responses
        enriched_query = f"Context:\n{context}\n\nQuestion: {query}"
        
        # Create the message in the thread
        await client.beta.threads.messages.create(
            thread_id = THREAD_ID,
            role = "user",
            content = enriched_query
        )
        print("Debug: Created message in thread")
        
        # Get the assistant ID
        assistant_id = await create_assistant()
        print(f"Debug: Got assistant ID: {assistant_id}")
        
        print("Debug: Starting stream...")
        async with client.beta.threads.runs.stream(
            thread_id = THREAD_ID,
            assistant_id = assistant_id,
            instructions = """
                    IMPORTANT ABOUT FORMATTING:

            You should respond with HTML formatting. Use the following HTML elements:
            - <h1> for main heading 
            - <h2> for subheadings
            - <p> for paragraphs
            - <ul> and <li> for bullet lists
            - <ol> and <li> for numbered lists
            - <a href="url"> for links
            - <strong> for emphasized text
            - <br> for line breaks where needed

            IMPORTANT:
            - DO NOT start the answer with ```html
            - DO NOT end the answer with ``
            - Use complete HTML tags (<ul><li>point</li></ul>, not just 'ul>')
            - DO NOT write 'ul>' separately  
            - DO NOT write 'ol>' separately

            Formatting example:
            <h1>Main Title</h1>
            <p>A paragraph of text that can contain <strong>emphasized text</strong> and <a href="https://ehelse.no">links</a>.</p>
            <h2>Subtitle</h2>
            <ul>
            <li>Point 1</li>
            <li>Point 2</li>
            </ul>
            """
        ) as stream:
            print("Debug: Stream created, waiting for chunks...")
            async for chunk in stream:
                print(f"Debug: Received chunk type: {type(chunk)}")
                print(f"Debug: Event type: {chunk.event}")
                
                # Let's add more detailed debugging of the chunk structure
                print(f"Debug: Full chunk data: {chunk}")
                
                if chunk.event == "thread.message.delta":
                    # Add debugging for the delta structure
                    print(f"Debug: Delta content: {chunk.data}")
                    if hasattr(chunk.data, 'delta') and chunk.data.delta:
                        if hasattr(chunk.data.delta, 'text'):
                            content = chunk.data.delta.text #Whats the problem here
                            print(f"Debug: Yielding content: {content}")
                            yield content
                        elif hasattr(chunk.data.delta, 'content'):
                            for content_block in chunk.data.delta.content:
                                if content_block.type == 'text':
                                    print(f"Debug: Yielding content block: {content_block.text.value}")
                                    yield content_block.text.value

    except Exception as e:
        error_message = f"Error in generate_response: {str(e)}"
        print(f"Debug: {error_message}")
        yield error_message

async def get_streaming_response(query: str) -> AsyncGenerator[str, None]:
  """
  Main function to handle the chat workflow
  """
  context = await get_relevant_context(query)
  async for token in generate_response(query, context):
      yield token
