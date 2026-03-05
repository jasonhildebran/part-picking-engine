from langgraph.graph import StateGraph, START, END
from schemas import ExecutionState, ComponentSchema, SourceTypeEnum

def mutate_state(state: ExecutionState, node_name: str) -> dict:
    print(f"--- Executing Node: {node_name} ---")
    return {"status": f"Processed by {node_name}"}

def triage_node(state: ExecutionState):
    return mutate_state(state, "Triage")

def tier1_api_search_node(state: ExecutionState):
    return mutate_state(state, "Tier1_API_Search")

def tier2_deep_scraper_node(state: ExecutionState):
    print("--- Executing Node: Tier2_Deep_Scraper ---")
    dummy_component = ComponentSchema(
        part_number="DUMMY-123",
        source_type=SourceTypeEnum.DEEP_SCRAPE,
        specs={"voltage": {"value": 12, "unit": "V"}}
    )
    return {
        "candidates_evaluated": state.candidates_evaluated + [dummy_component],
        "status": "Processed by Tier2_Deep_Scraper"
    }

def checker_node(state: ExecutionState):
    print("--- Executing Node: Checker ---")
    if getattr(state, "candidates_evaluated", None):
         return {"final_selection": state.candidates_evaluated[0], "status": "Processed by Checker"}
    return {"status": "Processed by Checker"}

def tier3_ingestion_node(state: ExecutionState):
    return mutate_state(state, "Tier3_Ingestion")

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
    
    # Simple heuristic to distinguish PDF ingestion vs text query
    if "pdf" in query or query.endswith(".pdf"):
        return "Tier3_Ingestion"
    return "Triage"

workflow = StateGraph(ExecutionState)

# Add all nodes
workflow.add_node("Triage", triage_node)
workflow.add_node("Tier1_API_Search", tier1_api_search_node)
workflow.add_node("Tier2_Deep_Scraper", tier2_deep_scraper_node)
workflow.add_node("Checker", checker_node)
workflow.add_node("Tier3_Ingestion", tier3_ingestion_node)

# START router
workflow.add_conditional_edges(
    START,
    start_router,
    {"Triage": "Triage", "Tier3_Ingestion": "Tier3_Ingestion"}
)

# 3-Tier path
workflow.add_edge("Triage", "Tier1_API_Search")
workflow.add_conditional_edges(
    "Tier1_API_Search",
    supervisor_router,
    {"Checker": "Checker", "Tier2_Deep_Scraper": "Tier2_Deep_Scraper"}
)
workflow.add_edge("Tier2_Deep_Scraper", "Checker")
workflow.add_edge("Checker", END)

# Tier 3 Path
workflow.add_edge("Tier3_Ingestion", END)

app = workflow.compile()
# Aliases so the current QA test still loads ingestion_app without breaking imports
main_app = app
ingestion_app = app

if __name__ == "__main__":
    print("LangGraph orchestration compiled.")
