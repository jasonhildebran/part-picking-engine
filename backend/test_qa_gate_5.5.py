import requests
import json

BASE_URL = "http://localhost:8000"

def run_live_graph_query(prompt_text, test_name):
    print(f"\n--- Running Test: {test_name} ---")
    print(f"Prompt: '{prompt_text}'")
    
    try:
        response = requests.post(
            f"{BASE_URL}/start_job", 
            json={"prompt": prompt_text}, 
            stream=True
        )
        
        assert response.status_code == 200, f"Failed: Expected 200, got {response.status_code}"
        
        print("Stream connected. Waiting for live LangGraph execution...\n")
        
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                # Optional: Strip "data: " prefix if your SSE formats it that way
                if decoded_line.startswith("data: "):
                    decoded_line = decoded_line[6:]
                
                try:
                    packet = json.loads(decoded_line)
                    print(f"[{packet.get('node', 'UNKNOWN')}] -> {packet.get('message', 'No message')}")
                    
                    # Print the final specs if the job is complete
                    if packet.get("status") == "complete" and "candidates_evaluated" in packet.get("state", {}):
                        candidates = packet["state"]["candidates_evaluated"]
                        if candidates:
                            print(f"\n✅ SUCCESS! Final Part Cached: {candidates[-1].get('name', 'Unknown')}")
                            print(f"Specs: {candidates[-1].get('specs', {})}")
                except json.JSONDecodeError:
                    print(f"Raw Stream: {decoded_line}")
                    
    except Exception as e:
        print(f"❌ Test Failed: {e}")

if __name__ == "__main__":
    # Test A: The Fast Lane (Should hit Nexar and skip Firecrawl)
    run_live_graph_query("Find a standard NE555 Timer IC", "Tier 1 Nexar Routing")
    
    # Test B: The Deep Fallback (Should fail Nexar and trigger Firecrawl)
    run_live_graph_query("Find a highly obscure 12V 300RPM brushed DC motor with a 4mm D-shaft", "Tier 2 Firecrawl Routing")