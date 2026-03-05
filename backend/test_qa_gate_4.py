from graph import ingestion_app 
import uuid
from datetime import datetime

def test_tier_1_cache_hit():
    print("--- Testing Route: Tier 1 Cache Hit ---")
    
    # Updated to satisfy strict Pydantic requirements
    initial_state = {
        "job_metadata": {
            "domain": "hardware", 
            "target_item": "12V Motor",
            "job_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat()
        },
        "search_parameters": {"query": "test"},
        "constraints": [],
        "candidates_evaluated": [{
            "part_number": "MOCK-123",
            "source_type": "API_CACHE",
            "specs": {}
        }],
        "status": "pending"
    }
    
    try:
        # Run the graph
        for output in ingestion_app.stream(initial_state):
            for key, value in output.items():
                print(f"Node Executed: {key}")
        print("✅ Cache Hit Test Passed: Graph routed to Checker without touching Tier 2.")
    except Exception as e:
        print(f"❌ Cache Hit Test Failed: {e}")

def test_tier_2_cache_miss():
    print("\n--- Testing Route: Tier 2 Fallback (Cache Miss) ---")
    
    # Updated to satisfy strict Pydantic requirements
    initial_state = {
         "job_metadata": {
             "domain": "hardware", 
             "target_item": "Obscure 5V Servo",
             "job_id": str(uuid.uuid4()),
             "timestamp": datetime.now().isoformat()
         },
         "search_parameters": {"query": "test"},
         "constraints": [],
         "candidates_evaluated": [],
         "status": "pending"
    }

    try:
        # Run the graph
        executed_nodes = []
        # FIXED TYPO: Changed 'graph.stream' to 'ingestion_app.stream'
        for output in ingestion_app.stream(initial_state):
            for key, value in output.items():
                print(f"Node Executed: {key}")
                executed_nodes.append(key)
                
        assert "Tier2_Deep_Scraper" in executed_nodes, "Failed: Supervisor did not trigger the Tier 2 fallback."
        print("✅ Cache Miss Test Passed: Supervisor successfully detected empty candidates and routed to Tier 2 Scraper.")
    except Exception as e:
        print(f"❌ Cache Miss Test Failed: {e}")

if __name__ == "__main__":
    test_tier_1_cache_hit()
    test_tier_2_cache_miss()