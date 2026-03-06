from database import SessionLocal
from models import ComponentVault, SourceType
import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_nexar_token():
    client_id = os.getenv("NEXAR_CLIENT_ID")
    client_secret = os.getenv("NEXAR_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError("Missing NEXAR_CLIENT_ID or NEXAR_CLIENT_SECRET in .env file.")
        
    url = "https://identity.nexar.com/connect/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    
    response = requests.post(url, data=data)
    response.raise_for_status()
    # E.g., {"access_token": "...", "expires_in": 86400, "token_type": "Bearer"}
    return response.json().get("access_token")

def test_tier_1_api_and_cache(part_number: str):
    print(f"--- Tier 1 Sandbox: Searching for {part_number} ---")
    
    # Check local SQLite vault first
    db = SessionLocal()
    try:
        cached_part = db.query(ComponentVault).filter(ComponentVault.part_number == part_number).first()
        
        if cached_part:
            print(f"✅ Cache Hit! Part found in SQLite Vault.")
            print(f"Name: {cached_part.name}")
            print(f"Source: {cached_part.source_type}")
            print(f"Specs: {json.dumps(cached_part.specs, indent=2)}")
            return cached_part
            
        print(f"❌ Cache Miss: Part not found locally.")
        
        # Mock querying Nexar API (formerly Octopart)
        print("Authenticating with Nexar (OAuth2)...")
        token = get_nexar_token()
        print("✅ Received Bearer Token.")
        
        print("Simulating GraphQL API call to Nexar...")
        # A simple query structure for Nexar
        query = '''
        query Search($mpn: String!) {
            supSearch(q: $mpn, limit: 1) {
                results {
                    part {
                        mpn
                        name
                        shortDescription
                    }
                }
            }
        }
        '''
        variables = {"mpn": part_number}
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # We perform a real request to validate authentication works!
        api_url = "https://api.nexar.com/graphql"
        response = requests.post(api_url, json={"query": query, "variables": variables}, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        print("✅ API Search successful. Received Data:")
        print(json.dumps(data, indent=2))
        
        # We return a mock parsed object anyway for standard formatting tests downstream
        mock_api_response = {
            "part_number": part_number,
            "name": "Simulated Nexar Component",
            "source_type": SourceType.API_CACHE,
            "specs": {
                "voltage": {"value": 5, "unit": "V"}
            }
        }
        return mock_api_response
    except Exception as e:
        print(f"❌ Tier 1 Error: {e}")
        return None
    finally:
        db.close()

if __name__ == "__main__":
    test_tier_1_api_and_cache("TEST-MTR-001")
    print("\n--- Next Query ---")
    test_tier_1_api_and_cache("NEW-UNKNOWN-PART-999")
