import os
import json
from dotenv import load_dotenv
from database import SessionLocal
from models import ComponentVault, SourceType
from schemas import ComponentSchema, SourceTypeEnum
from firecrawl import FirecrawlApp
from google import genai

load_dotenv()

def test_tier_2_deep_scrape(url: str):
    print(f"--- Tier 2 Sandbox: Scraper & Data Extraction ---")
    print(f"Target URL: {url}")
    print("Model: gemini-2.5-flash")
    
    # 1. Scrape with Firecrawl
    print("\nSimulating Firecrawl scrape...")
    firecrawl_app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
    try:
        scrape_result = firecrawl_app.scrape(url, formats=['markdown'])
        markdown_content = scrape_result.markdown if hasattr(scrape_result, "markdown") else ""
        if not markdown_content:
             print("❌ Failed to extract markdown from Firecrawl.")
             return
        print(f"✅ Extracted {len(markdown_content)} characters of markdown.")
    except Exception as e:
        print(f"❌ Firecrawl scraping failed: {e}")
        return

    # 2. Extract with Gemini 3 Flash
    system_prompt = (
        "You are an expert hardware component scraper. Extract component data from web search results. "
        "You must convert any extracted Imperial or non-standard metric units into SI standard units (Nm, mm, V) before formatting your JSON output. "
        "Return a raw, valid JSON object that strictly matches the ComponentSchema structure containing: "
        "'part_number' (string), 'name' (string), 'source_type' (string, e.g., 'DEEP_SCRAPE'), and 'specs' (a standard dictionary of physical or electrical properties containing a 'value' and 'unit')."
    )
    
    print(f"\nSystem Prompt:\n{system_prompt}\n")
    print("Calling gemini-3-flash...")
    
    genai_client = genai.Client()
    
    try:
        response = genai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=markdown_content,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.1
            ),
        )
        # Parse the JSON matching our Pydantic schema
        extracted_json = json.loads(response.text)
        
        # Override source type just to be safe
        extracted_json["source_type"] = SourceTypeEnum.DEEP_SCRAPE.value
        
        # Validate with Pydantic
        validated_data = ComponentSchema(**extracted_json)
        print("✅ Pydantic validation passed.")
        print(validated_data.model_dump_json(indent=2))
        
    except Exception as e:
         print(f"❌ Gemini extraction or Pydantic validation failed: {e}")
         return
         
    # 3. Insert to database
    db = SessionLocal()
    try:
        # Check if exists to avoid unique constraint error
        existing = db.query(ComponentVault).filter(ComponentVault.part_number == validated_data.part_number).first()
        if not existing:
            new_part = ComponentVault(
                part_number=validated_data.part_number,
                name=validated_data.name,
                source_type=SourceType(validated_data.source_type.value),
                specs=validated_data.specs
            )
            db.add(new_part)
            db.commit()
            print("\n✅ Successfully cached deeply scraped part into SQLite Vault.")
        else:
            print("\nPart already in DB.")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Failed to insert into DB: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # A dummy URL for testing the flow
    test_tier_2_deep_scrape("https://www.adafruit.com/product/169")
