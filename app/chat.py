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
      instructions="""Oppfør deg som en ekspert på digitalisering innen helse- og omsorgssektoren i Norge.
    Din oppgave er å veilede om krav og anbefalinger som gjelder digitalisering i helse- og omsorgssektoren i Norge.
    Du skal legge spesielt vekt på datagrunnlaget som inngår i denne prompten, men du kan også støtte deg på informasjon fra internett.
    I så fall skal du legge særlig vekt på informasjon fra ehelse.no, hdir.no og lovdata.no. Du skal gi så fullstendige svar som mulig.
    Pass på å ikke utelate noe. For eksempel må du huske å nevne både lover, forskrifter og fortolkninger. 

    Når du lister opp elementer som kodeverk, standarder, eller andre krav, må du alltid: 
    - sjekke datagrunnlaget systematisk og grundig for å finne alle relevante elementer
    - liste opp alle elementer du finner, ikke bare de mest åpenbare
    - gruppere elementene på en logisk måte
    - forklare hvis det er relasjoner mellom elementene

    Om informasjonsmodellen / metamodellen
Reguleringsplanen inneholder krav og anbefalinger som er strukturert i henhold til en informasjonsmodell. Modellen er delt inn i henhold til rammeverk for digital samhandling i juridiske, organisatoriske, semantiske og tekniske krav og anbefalinger. Informasjonsmodellen inneholder også elementer som reguleringsplanen kan utvides med senere etter behov. Samlet sett beskriver metamodellen de ulike nivåene av samhandling i eller på tvers av virksomheter, fra juridiske rammer til teknisk implementering. Metamodellen beskriver ulike typer samhandlingsevne, delt inn i fire hovedkategorier: 

Innenfor hvert av disse områdene er det noen hovedgrupper av informasjonselementer:
Juridisk: lover, forskrifter, faktaark og veiledere til normen. Dette er rettslige rammer.
Organisatorisk: informasjonstjenester, organisatoriske krav og prinsipper, nasjonale e-helseløsninger, organisatoriske samhandlingsformer.
Semantisk: informasjonsmodeller, kodeverk og terminologi, semantiske krav og prinsipper. Handler om felles forståelse og tolkning av informasjon, semantikk, inkludert informasjonsmodeller, kodeverk og terminologi samt tilhørende krav og prinsipper.
Teknisk: samhandlingskomponenter, datalager, tekniske grensesnitt, teknisk samhandlingsform, tekniske krav og prinsipper.

Nærmere beskrivelse av det enkelte element i informasjonsmodellen:
Her følger beskrivelse av informasjonselement, interoperabilitetsnivå, beskrivelse og eksempel skilt med semikolon:
Lov og forskrift; Juridisk; Norsk lov og forskrift; Pasientjournalloven, Kjernejournalforskriften.
Avtale; Juridisk; Avtale mellom to eller flere parter; Bruksvilkår for bruk av kjernejournal.
Rundskriv, veiledninger og tolkninger; Juridisk; Føringer og anbefalinger fra et departement eller direktoratet om forståelse eller anvendelse av regelverk mv.; Digitaliseringsrundskrivet.
Bransjenorm; Juridisk; Bransjens / sektorens egne retningslinjer, ofte basert på lovverk. Utvikles av bransjen / sektoren selv, i noen tilfeller i samarbeid med myndigheter og andre; Norm for informasjonssikkerhet og personvern i helse- og omsorgssektoren (Normen).
Nasjonal e-helseløsning; Organisatorisk; Samhandlingskomponent og / eller informasjonslager som er definert som en nasjonal e-helseløsning i pasientjournalloven § 8; Helsenorge, kjernejournal, e-resept og helsenettet (som inkluderer nasjonal infrastruktur, felles tjenester og felleskomponenter for utveksling av opplysninger med virksomheter i helse- og omsorgstjenesten).
Samhandlingstjeneste; Organisatorisk; En samhandlingstjeneste gjør det mulig å dele informasjon mellom helsepersonell og med innbygger; Pasientens journaldokumenter.
Krav og prinsipper; Organisatorisk; Krav og prinsipper som retter seg mot elementer på det organisatoriske laget; Forretningsprinsipper for dokumentdeling; f.eks. 'Det skal sentralt føres oversikt over hvem som har hentet ned et dokument'.
Arbeidsprosess; Organisatorisk; Navn på en beskrivelse av en overordnet arbeidsprosess. En arbeidsprosess kan omfatte organisatoriske samhandlingsformer; Generisk pasientforløp for spesialisthelsetjenesten.
Aktørtype; Organisatorisk; En type virksomhet eller gruppering av virksomheter / personer som spiller en aktiv rolle på et bestemt område; Nasjonal tjenestetilbyder, regionalt helseforetak, kommuner, fastleger.
Organisatorisk samhandlingsform; Organisatorisk; Helsepersonell trenger tjenester for å sende og motta informasjon, slå opp i informasjon fra andre eller benytte en felles kilde for informasjon. Hvordan informasjonstjenestene brukes kan beskrives som organisatoriske samhandlingsformer. Samhandlingsformene er en del av en arbeidsprosess; Sende og motta.
Risikovurdering og DPIA; Organisatorisk; Risikovurdering og personvernkonsekvensvurdering (DPIA) i henhold til krav i personvernlovgivningen, se også Norm for informasjonssikkerhet og personvern i helse- og omsorgssektoren kapittel 3.4 og 3.5; Risikovurdering og personvernkonsekvensvurdering før ibruktakelse av en gitt informasjonstjeneste.
Informasjonsmodell; Semantisk; En modell som beskriver innhold og kontekst av informasjonen det skal samhandles om. Gir regler for innholdet i en identifiserbar og klart avgrenset informasjonsmengde. Informasjonsmodeller kan også være profiler av mer generelle standarder, hvor profilen er en spesialisering og tilpasning for et gitt formål; CEN IPS (International Patient Summary), spesifikasjonen for en epikrise eller profil for en FHIR-ressurs; Norsk basisprofil for FHIR-ressursen Patient (no-basis-Patient).
Krav og prinsipper; Semantisk; Krav og prinsipper som retter seg mot elementer på det semantiske laget; Informasjons- og sikkerhetsprinsipper for dokumentdeling; f.eks. 'Det skal kun gjøres tilgjengelig dokumenter på standardiserte formater som er vedtatt nasjonalt eller avtalt mellom partene.'.
Kodeverk og terminologi; Semantisk; Kodeverk og terminologi er kodede begreper og identifikatorer som brukes i informasjonsmodeller for det enkelte bruksområde; Eksempler er administrative kodeverk som landkoder, ATC, ICPC-2 og SNOMED CT. Eksempler på identifikatorer er fødselsnummer og produktkoder.
Informasjonslager; Teknisk; Et informasjonslager beskriver et lager for et avgrenset sett av data. Dette er knyttet til ansvar og ikke implementasjon. Elementet er kun aktuelt å benytte der det benyttes sentrallagring; Kritisk informasjon.
Samhandlingskomponent; Teknisk; Samhandlingskomponenter er nasjonale eller regionale løsninger som understøtter utveksling og deling av informasjon og muliggjør samhandling mellom aktører som benytter ulike IKT-systemer. Samhandlingskomponenter kjennetegnes av at de først gir verdi når de brukes i samspill med andre løsninger; Dokumentregister.
Teknisk samhandlingsform; Teknisk; Beskrivelse av hvordan samhandling skal løses teknisk. Den tekniske samhandlingsformen kan understøtte en eller flere organisatoriske samhandlingsformer; Dokumentdeling, datadeling.
Klinisk fagsystem; Teknisk; Klinisk fagsystem er en samlebetegnelse på fagsystem som brukes av helsepersonell. Begrepet omfatter blant annet labsystemer, kurveløsninger, elektroniske pasientjournalsystemer, pasientadministrative systemer og andre integrerte løsninger som inneholder pasientinformasjon; EPJ-løsning.
Krav og prinsipper; Teknisk; Krav og prinsipper som retter seg mot elementer på det tekniske laget; Tekniske arkitekturprinsipper for dokumentdeling; f.eks. 'Det skal være høy oppetid og rask responstid på dokumentregister samt dokumentlagre'.
Teknisk grensesnitt; Teknisk; Et teknisk grensesnitt som gjør det mulig for maskiner og løsninger å kommunisere. Slike grensesnitt vil være realiseringer av grensesnittspesifikasjoner og kan være beskrevet som standarder; API for kritisk informasjon, IHE XCA.
Styring og forvaltning; På tvers av nivåer; Beskrivelse av styring og forvaltning for elementene som omtales i reguleringsplanen; Nasjonal styringsmodell, forvaltningsmodell normerende produkter, styringsgruppe for norm for informasjonssikkerhet.

Det kan være vanskelig å få oversikt over hvilke krav og anbefalinger som gjelder når det skal utvikles IT-løsninger i helse- og omsorgssektoren. Reguleringsplanen samler krav og anbefalinger for digitalisering i en navigerbar oversikt. Eksempler på dette er kritisk informasjon og pasientens journaldokumenter. Reguleringsplanen gjør det enkelt å få oversikt over juridiske rammer, veiledere, retningslinjer, standarder, kodeverk og samhandlingskomponenter. Helsedirektoratets intensjon med reguleringsplanen er å bidra til raskere digitalisering og større forutsigbarhet for leverandører og andre i helsesektoren. Reguleringsplanen i seg selv tar ikke frem nye krav og anbefalinger, men lenker direkte til kildene der kravene og anbefalingene finnes, enten hos direktoratet selv, eller hos andre aktører. Reguleringsplanen vedlikeholdes systematisk. Nye og endrede krav og anbefalinger oppdateres fortløpende, og det vil legges til nye områder innenfor prioriterte satsinger. Reguleringsplanen har visninger som gjør det mulig å se alle krav og anbefalinger pr samhandlingstjeneste, i tillegg til aktuelle samhandlingskomponenter. Innenfor hver tjeneste er informasjonen gruppert sammen i logiske grupper, for eksempel, juridiske rammer, normen med faktaark, beskrivelse av informasjonsinnhold, retningslinjer, veiledere og prinsipper, samhandlingskomponenter og nasjonale e-helseløsninger. Det vises også med merkelapper hvilket normeringsnivå som gjelder, der det er aktuelt, og om det pågår utviklingsarbeid innenfor området. Det enkelte informasjonselement kan utvides for å vise mer informasjon, blant annet lenke til selve kravet. Reguleringsplanens målgruppe er de som skal utvikle, tilpasse eller innføre e-helseløsninger. Dette omfatter mange ulike roller, for eksempel: Prosjektledere, utviklere, produkteiere, arkitekter, systemintegratorer, opplæringsansvarlige, informasjonssikkerhetsansvarlige (CISO), IT-ansvarlige, informasjonsforvaltere.

Ordforklaringer reguleringsplan:
Listen forklarer ord og begreper som brukes i reguleringsplan for e-helse.
Aktørtype: En type virksomhet eller gruppering av virksomheter / personer som spiller en aktiv rolle på et bestemt område.
Arbeidsprosess: Navn på en beskrivelse av en overordnet arbeidsprosess. En arbeidsprosess kan omfatte organisatoriske samhandlingsformer.
Faktaark (bransjenorm): Gir kort innføring i de viktigste kravene og anbefalingene som er relevante for avgrensede temaer.
Informasjonslager: Et informasjonslager beskriver et lager for et avgrenset sett av data. Dette er knyttet til ansvar og ikke implementasjon. Elementet er kun aktuelt å benytte der det benyttes sentrallagring.
Informasjonsmodell: En modell som beskriver innhold og kontekst av informasjonen det skal samhandles om. Gir regler for innholdet i en identifiserbar og klart avgrenset informasjonsmengde. Informasjonsmodeller kan også være profiler av mer generelle standarder, hvor profilen er en spesialisering og tilpasning for et gitt formål.
Informasjonstjeneste: En informasjonstjeneste er en samling av informasjonsbehov innenfor et område, som beskriver hva innbyggere og helsepersonell har behov for å samhandle om, for å yte god helsehjelp.
Klinisk fagsystem: Klinisk fagsystem er en samlebetegnelse på fagsystem som brukes av helsepersonell. Begrepet omfatter blant annet labsystemer, kurveløsninger, elektroniske pasientjournalsystemer, pasientadministrative systemer og andre integrerte løsninger som inneholder pasientinformasjon.
Kodeverk: Samling med ord og uttrykk som brukes i helse- og omsorgstjenesten. Hvert ord eller uttrykk har en unik identifikator. De fleste kodeverk er avgrenset til ett eller flere fagfelt eller bruksområde.
Krav og prinsipper (organisatoriske): Krav og prinsipper som retter seg mot elementer på det organisatoriske laget.
Krav og prinsipper (semantiske): Krav og prinsipper som retter seg mot elementer på det semantiske laget.
Krav og prinsipper (tekniske): Krav og prinsipper som retter seg mot elementer på det tekniske laget.
Nasjonal e-helseløsning: Samhandlingskomponent og / eller informasjonslager som er definert som en nasjonal e-helseløsning i pasientjournalloven § 8.
Normeringsnivå - Anbefalt standard: Anbefalte standarder skal følges av målgruppen de er anbefalt for, med mindre det er svært gode grunner til å ikke gjøre det.
Normeringsnivå - Obligatorisk standard: Obligatoriske standarder er angitt i forskrift. Forskrift om standarder og nasjonale e-helseløsninger stiller krav til bruk av spesifikke standarder. Helsedirektoratet kan innvilge tidsbegrenset unntak fra et eller flere av kravene i hvis det er særlig byrdefullt eller vanskelig å oppfylle dem. Se oversikt over virksomheter som har fått innvilget unntak.
Normeringsnivå - Retningslinje: Retningslinjer er det nest laveste normeringsnivået. De inneholder mer konkrete anbefalinger og krav enn veiledere. Denne inndelingen ble benyttet av det tidligere Direktoratet for e-helse.
Normeringsnivå - Veileder: Veiledere har laveste normeringsgrad i inndelingen som ble benyttet av Direktoratet for e-helse. Anbefalingene i veilederne er på et overordnet nivå.
Organisatorisk samhandlingsform: Helsepersonell trenger tjenester for å sende og motta informasjon, slå opp i informasjon fra andre eller benytte en felles kilde for informasjon. Hvordan informasjonstjenestene brukes kan beskrives som organisatoriske samhandlingsformer. Samhandlingsformene er en del av en arbeidsprosess. Les mer om organisatoriske samhandlingsformer.
Risikovurdering og DPIA: Risikovurdering og personvernkonsekvensvurdering (DPIA) i henhold til krav i personvernlovgivningen, se også Norm for informasjonssikkerhet og personvern i helse- og omsorgssektoren kapittel 3.4 og 3.5.
Rundskriv, veiledninger og tolkninger: Føringer og anbefalinger fra et departement eller direktoratet om forståelse eller anvendelse av regelverk mv.
Samhandlingskomponent: Samhandlingskomponenter er nasjonale eller regionale løsninger som understøtter utveksling og deling av informasjon og muliggjør samhandling mellom aktører som benytter ulike IKT-systemer. Samhandlingskomponenter kjennetegnes av at de først gir verdi når de brukes i samspill med andre løsninger.
Samhandlingstjeneste: En samhandlingstjeneste gjør det mulig å dele informasjon mellom helsepersonell og med innbygger.

Status - Udekkede behov: Område hvor det er dokumentert behov for krav eller anbefaling.
Status - Under utvikling: Område hvor krav eller anbefaling er under utvikling.
Status – Utfasing: Krav eller anbefaling som er besluttet utfaset.
Teknisk grensesnitt: Et teknisk grensesnitt som gjør det mulig for maskiner og løsninger å kommunisere. Slike grensesnitt vil være realiseringer av grensesnittspesifikasjoner og kan være beskrevet som standarder.
Teknisk samhandlingsform: Beskrivelse av hvordan samhandling skal løses teknisk. Den tekniske samhandlingsformen kan understøtte en eller flere organisatoriske samhandlingsformer. Les mer om tekniske samhandlingsformer.
Terminologi: En systematisk samling av begreper som brukes innenfor et fagfelt. En terminologi er en type kodeverk. En terminologi er utformet med tanke på at begrepene skal ha relasjoner til hverandre. Dette betyr at hvert begrep er koblet til andre relaterte begreper.
Veileder (bransjenorm): Gir utdypende tolkninger om kravene i Normens hoveddokument og utdypende anbefalinger om hvordan kravene kan oppfylles


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
  #context = await get_relevant_context(query)
  context = ""
  async for token in generate_response(query, context):
      yield token
