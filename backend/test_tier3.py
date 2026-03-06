import os
import json
import time
from dotenv import load_dotenv
from database import SessionLocal
from models import ComponentVault, SourceType
from schemas import ComponentSchema, SourceTypeEnum
from google import genai

load_dotenv()

def test_tier_3_pdf_ingestion(pdf_path: str):
    print(f"--- Tier 3 Sandbox: PDF Ingestion ---")
    print(f"PDF Path: {pdf_path}")
    print("Model: gemini-2.5-flash")
    
    genai_client = genai.Client()
    
    print("\nUploading to Gemini File API...")
    try:
        uploaded_file = genai_client.files.upload(file=pdf_path)
        print(f"✅ Uploaded file: {uploaded_file.name}")
        
        # Give API a moment to process the file
        while uploaded_file.state.name == "PROCESSING":
            print('Processing file...', end='\r')
            time.sleep(2)
            uploaded_file = genai_client.files.get(name=uploaded_file.name)
            
        if uploaded_file.state.name == "FAILED":
             raise Exception("File processing failed.")
    except Exception as e:
        print(f"❌ Failed to upload PDF: {e}")
        return

    system_prompt = (
        "You are an expert hardware engineer. Extract component specifications directly from datasheets. "
        "You must convert any extracted Imperial or non-standard metric units into SI standard units (Nm, mm, V) before formatting your JSON output. "
        "Return a raw, valid JSON object that strictly matches the ComponentSchema structure containing: "
        "'part_number' (string), 'name' (string), 'source_type' (string, e.g., 'USER_UPLOAD'), and 'specs' (a standard dictionary of physical or electrical properties containing a 'value' and 'unit')."
    )
    
    print(f"\nSystem Prompt:\n{system_prompt}\n")
    print("Calling gemini-2.5-flash...")
    
    try:
        response = genai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[uploaded_file, "Extract the component specifications from this document."],
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.1
            ),
        )
        
        extracted_json = json.loads(response.text)
        extracted_json["source_type"] = SourceTypeEnum.USER_UPLOAD.value
        
        # Validate with Pydantic
        validated_data = ComponentSchema(**extracted_json)
        print("✅ Pydantic validation passed.")
        print(validated_data.model_dump_json(indent=2))
        
    except Exception as e:
        print(f"❌ Gemini extraction or Pydantic validation failed: {e}")
        genai_client.files.delete(name=uploaded_file.name)
        return
        
    # Cleanup file
    genai_client.files.delete(name=uploaded_file.name)
    print("✅ Cleaned up file from Gemini.")
        
    # Insert to database
    db = SessionLocal()
    try:
        # Check if exists
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
            print("\n✅ Successfully cached PDF-extracted part into SQLite Vault.")
        else:
            print("\nPart already in DB.")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Failed to insert into DB: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    dummy_pdf = "temp/dummy_datasheet.pdf"
    os.makedirs("temp", exist_ok=True)
    with open(dummy_pdf, "wb") as f:
        # Write minimal valid PDF content for API acceptance
        f.write(b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n0000000115 00000 n\ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n188\n%%EOF\n")
        
    test_tier_3_pdf_ingestion(dummy_pdf)
