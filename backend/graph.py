import os
import json
import time
import requests
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from schemas import ExecutionState, ComponentSchema, SourceTypeEnum
from database import SessionLocal
from models import ComponentVault, SourceType
from firecrawl import FirecrawlApp
from google import genai

load_dotenv()

def get_nexar_token():
    client_id = os.getenv("NEXAR_CLIENT_ID")
    client_secret = os.getenv("NEXAR_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError("Missing NEXAR_CLIENT_ID or NEXAR_CLIENT_SECRET")
    url = "https://identity.nexar.com/connect/token"
    response = requests.post(url, data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret})
    response.raise_for_status()
    return response.json().get("access_token")

def triage_node(state: ExecutionState):
    print("--- Executing Node: Triage ---")
    return {"status": "Processed by Triage"}

def nexar_search_node(state: ExecutionState):
    print("--- Executing Node: Tier1_API_Search (nexar_search_node) ---")
    query = ""
    if getattr(state, "search_parameters", None) and getattr(state.search_parameters, "query", None):
        query = state.search_parameters.query
    part_number = query if query else "UNKNOWN-PART"
    
    db = SessionLocal()
    try:
        cached_part = db.query(ComponentVault).filter(ComponentVault.part_number == part_number).first()
        if cached_part:
            print("✅ Cache Hit!")
            component = ComponentSchema(
                part_number=cached_part.part_number,
                name=cached_part.name,
                source_type=cached_part.source_type.value,
                specs=cached_part.specs
            )
            return {"candidates_evaluated": state.candidates_evaluated + [component], "status": "Processed by Tier1 (Cache Hit)"}
            
        print("❌ Cache Miss. Authenticating with Nexar (OAuth2)...")
        token = get_nexar_token()
        
        graphql_query = '''
        query Search($mpn: String!) {
            supSearch(q: $mpn, limit: 1) {
                results {
                    part { mpn name }
                }
            }
        }
        ''' # Simple mock handling for now
        api_url = "https://api.nexar.com/graphql"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        response = requests.post(api_url, json={"query": graphql_query, "variables": {"mpn": part_number}}, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if "errors" in data or not data.get("data") or not data["data"].get("supSearch") or not data["data"]["supSearch"].get("results"):
            print("❌ API returned no results or rate limit exceeded.")
            return {"status": "Tier1 Failed: No Part Found or Error"}

        part_data = data["data"]["supSearch"]["results"][0]["part"]
        
        component = ComponentSchema(
            part_number=part_data.get("mpn", part_number),
            name=part_data.get("name", "Unknown Part"),
            source_type=SourceTypeEnum.API_CACHE.value,
            specs={"shortDescription": {"value": part_data.get("shortDescription", ""), "unit": ""}}
        )
        
        existing = db.query(ComponentVault).filter(ComponentVault.part_number == component.part_number).first()
        if not existing:
            new_part = ComponentVault(part_number=component.part_number, name=component.name, source_type=SourceType(component.source_type.value), specs=component.specs)
            db.add(new_part)
            db.commit()
            
        return {"candidates_evaluated": state.candidates_evaluated + [component], "status": "Processed by Tier1 (API Hit)"}
        
    except Exception as e:
        print(f"❌ Tier 1 Error: {e}")
        return {"status": f"Tier1 Failed: {str(e)}"}
    finally:
        db.close()

def deep_scrape_node(state: ExecutionState):
    print("--- Executing Node: Tier2_Deep_Scraper (deep_scrape_node) ---")
    query = ""
    if getattr(state, "search_parameters", None) and getattr(state.search_parameters, "query", None):
        query = state.search_parameters.query
        
    url = query if "http" in query else None
    
    db = SessionLocal()
    try:
        firecrawl_app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
        
        if not url:
            print(f"Determining URL via Firecrawl Search for: '{query}'")
            search_res = firecrawl_app.search(query, limit=1)
            if search_res and getattr(search_res, 'web', None) and len(search_res.web) > 0:
                url = search_res.web[0].url
                print(f"✅ Found supplier URL: {url}")
            else:
                raise ValueError("Could not find a relevant supplier URL for the query.")
                
        print("\nSimulating Firecrawl scrape...")
        scrape_result = firecrawl_app.scrape(url, formats=['markdown'])
        markdown_content = scrape_result.markdown if hasattr(scrape_result, "markdown") else ""
        if not markdown_content:
            raise ValueError("Failed to extract markdown from Firecrawl.")
            
        system_prompt = (
            "You are an expert hardware component scraper. Extract component data from web search results. "
            "You must convert any extracted Imperial or non-standard metric units into SI standard units (Nm, mm, V) before formatting your JSON output. "
            "Return a raw, valid JSON object that strictly matches the ComponentSchema structure containing: "
            "'part_number' (string), 'name' (string), 'source_type' (string, e.g., 'DEEP_SCRAPE'), and 'specs' (a standard dictionary of physical or electrical properties containing a 'value' and 'unit')."
        )
        
        genai_client = genai.Client()
        response = genai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=markdown_content,
            config=genai.types.GenerateContentConfig(system_instruction=system_prompt, response_mime_type="application/json", temperature=0.1)
        )
        extracted_json = json.loads(response.text)
        extracted_json["source_type"] = SourceTypeEnum.DEEP_SCRAPE.value
        component = ComponentSchema(**extracted_json)
        
        existing = db.query(ComponentVault).filter(ComponentVault.part_number == component.part_number).first()
        if not existing:
            new_part = ComponentVault(part_number=component.part_number, name=component.name, source_type=SourceType(component.source_type.value), specs=component.specs)
            db.add(new_part)
            db.commit()
            
        return {"candidates_evaluated": state.candidates_evaluated + [component], "status": "Processed by Tier2_Deep_Scraper"}
    except Exception as e:
        print(f"❌ Tier 2 Error: {e}")
        return {"status": f"Tier2 Failed: {str(e)}"}
    finally:
        db.close()

def pdf_ingestion_node(state: ExecutionState):
    print("--- Executing Node: Tier3_Ingestion (pdf_ingestion_node) ---")
    query = ""
    if getattr(state, "search_parameters", None) and getattr(state.search_parameters, "query", None):
        query = state.search_parameters.query
    pdf_path = query if ".pdf" in query else "temp/dummy_datasheet.pdf"
    
    db = SessionLocal()
    try:
        genai_client = genai.Client()
        uploaded_file = genai_client.files.upload(file=pdf_path)
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(2)
            uploaded_file = genai_client.files.get(name=uploaded_file.name)
        if uploaded_file.state.name == "FAILED":
             raise Exception("File processing failed.")
             
        system_prompt = (
            "You are an expert hardware engineer. Extract component specifications directly from datasheets. "
            "You must convert any extracted Imperial or non-standard metric units into SI standard units (Nm, mm, V) before formatting your JSON output. "
            "Return a raw, valid JSON object that strictly matches the ComponentSchema structure containing: "
            "'part_number' (string), 'name' (string), 'source_type' (string, e.g., 'USER_UPLOAD'), and 'specs' (a standard dictionary of physical or electrical properties containing a 'value' and 'unit')."
        )
        response = genai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[uploaded_file, "Extract the component specifications from this document."],
            config=genai.types.GenerateContentConfig(system_instruction=system_prompt, response_mime_type="application/json", temperature=0.1)
        )
        extracted_json = json.loads(response.text)
        extracted_json["source_type"] = SourceTypeEnum.USER_UPLOAD.value
        component = ComponentSchema(**extracted_json)
        
        genai_client.files.delete(name=uploaded_file.name)
        
        existing = db.query(ComponentVault).filter(ComponentVault.part_number == component.part_number).first()
        if not existing:
            new_part = ComponentVault(part_number=component.part_number, name=component.name, source_type=SourceType(component.source_type.value), specs=component.specs)
            db.add(new_part)
            db.commit()
            
        return {"candidates_evaluated": state.candidates_evaluated + [component], "status": "Processed by Tier3_Ingestion"}
    except Exception as e:
        print(f"❌ Tier 3 Error: {e}")
        return {"status": f"Tier3 Failed: {str(e)}"}
    finally:
        db.close()

def checker_node(state: ExecutionState):
    print("--- Executing Node: Checker ---")
    if getattr(state, "candidates_evaluated", None):
         return {"final_selection": state.candidates_evaluated[0], "status": "Processed by Checker"}
    return {"status": "Processed by Checker"}

def supervisor_router(state: ExecutionState) -> str:
    print("--- Executing Supervisor Router ---")
    candidates = getattr(state, "candidates_evaluated", [])
    if candidates and len(candidates) > 0:
        print("Supervisor routing to: Checker (Cache Hit)")
        return "Checker"
    else:
        print("Supervisor routing to: Tier2_Deep_Scraper (Cache Miss)")
        return "Tier2_Deep_Scraper"

def start_router(state: ExecutionState) -> str:
    query = ""
    if getattr(state, "search_parameters", None) and getattr(state.search_parameters, "query", None):
        query = state.search_parameters.query.lower()
    
    if "pdf" in query or query.endswith(".pdf"):
        return "Tier3_Ingestion"
    return "Triage"

workflow = StateGraph(ExecutionState)

workflow.add_node("Triage", triage_node)
workflow.add_node("Tier1_API_Search", nexar_search_node)
workflow.add_node("Tier2_Deep_Scraper", deep_scrape_node)
workflow.add_node("Checker", checker_node)
workflow.add_node("Tier3_Ingestion", pdf_ingestion_node)

workflow.add_conditional_edges(START, start_router, {"Triage": "Triage", "Tier3_Ingestion": "Tier3_Ingestion"})
workflow.add_edge("Triage", "Tier1_API_Search")
workflow.add_conditional_edges("Tier1_API_Search", supervisor_router, {"Checker": "Checker", "Tier2_Deep_Scraper": "Tier2_Deep_Scraper"})
workflow.add_edge("Tier2_Deep_Scraper", "Checker")
workflow.add_edge("Checker", END)
workflow.add_edge("Tier3_Ingestion", END)

app = workflow.compile()
main_app = app
ingestion_app = app

if __name__ == "__main__":
    print("LangGraph orchestration compiled.")
