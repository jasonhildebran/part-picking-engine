# ARCHITECTURE.md
## Core Application: Multi-Agent Hardware Procurement & Observability Tuner

### Architecture Overview
This application utilizes a decoupled React/FastAPI stack. It features a 3-Tier Fallback Multi-Agent architecture managed by LangGraph, designed to source, validate, and cache hardware components using strict data normalization. 

---

### Step 1: Environment & Infrastructure Scaffolding
* **Goal:** Initialize independent React (Vite/TypeScript) and FastAPI (Python) repositories. Set up dependency management, environment variables, the SQLite database, and file-handling libraries (`python-multipart`).
* **Why:** Establishes strict frontend/backend boundaries and prepares the server for the Tier 3 PDF Ingestion pipeline.
* **Testing Protocol (QA Gate 1):**
    * **Black Box:** Running dev scripts starts both servers on independent ports. Hitting the `/health` endpoint returns `200 OK`.
    * **White Box:** Verify SQLite `.db` file generation, secure `.env` configuration, and the presence of a secure temporary directory for incoming PDF uploads.

### Step 2: Data Models & State Schemas (The Blackboard & The Vault)
* **Goal:** Write Pydantic schemas for the runtime "Blackboard" and SQLAlchemy models for the "Component Vault" (including a `source_type` enum: `API_CACHE`, `DEEP_SCRAPE`, `USER_UPLOAD`).
* **Rule (Data Normalization):** All Pydantic schemas MUST utilize V2 `@field_validator` decorators to intercept and force incoming data into SI standard units (Torque = Nm, Dimensions = mm, Potential = V). The ComponentVault SQLAlchemy model must use a hybrid structure. It requires strict columns for identifiers (id, part_number, name, source_type) and a JSON column named specs to store the highly variable, normalized SI metric data.
* **Why:** Forcing strict schema compliance and unit normalization prevents hallucinated or misaligned data from poisoning the local caching database.
* **Testing Protocol (QA Gate 2):**
    * **Black Box:** Instantiate the Pydantic Blackboard with mock data (pass) and invalid data (throw strict `ValidationError`). Write and retrieve a mock component from the SQLite Vault.
    * **White Box:** Verify correct type hinting, SQLAlchemy unique constraints (preventing duplicate parts), and the active conversion logic within the `@field_validator` functions.

### Step 3: Core API Bridge & Streaming Foundation
* **Goal:** Build the `POST /start_job` route for the main orchestration loop, establish the Server-Sent Events (SSE) pipeline, and add a `POST /ingest_pdf` route for Tier 3.
* **Why:** The SSE stream drives the real-time observability dashboard. The dedicated PDF endpoint ensures direct routing to the specialized ingestion workflow.
* **Testing Protocol (QA Gate 3):**
    * **Black Box:** POST to `/start_job` returns `200 OK` followed by a staggered stream of `text/event-stream` mock packets. POST a sample PDF to `/ingest_pdf` returns `200 OK` and saves the file locally.
    * **White Box:** Review FastAPI routes for asynchronous `yield` generators. Ensure the PDF upload route validates file size and `.pdf` MIME types.

### Step 4: Agent Orchestration Logic (3-Tier LangGraph Routing)
* **Goal:** Construct the physical LangGraph state machine. Define nodes: `Triage`, `Tier1_API_Search`, `Tier2_Deep_Scraper`, `Checker`, `Supervisor`, and `Tier3_Ingestion`. Mock their internal logic.
* **Routing Logic:** Supervisor MUST route to `Tier1_API_Search` first. If state returns empty, conditionally route to `Tier2_Deep_Scraper`. `Tier3_Ingestion` operates as a standalone pipeline.
* **Why:** Builds the fallback brain and recursion guardrails without risking API costs on hallucinated loops.
* **Testing Protocol (QA Gate 4):**
    * **Black Box:** Test Cache Hit (Tier 1 -> Checker -> End) and Cache Miss (Tier 1 -> Supervisor -> Tier 2 -> Checker -> End).
    * **White Box:** Ensure conditional edges accurately evaluate the `candidates_evaluated` array before triggering the fallback scraper.

### Step 5: LLM Integration, Tool Binding & Prototype Sandbox
* **Goal:** Validate tools in isolated Python scripts (Sandbox). Connect LangGraph nodes to Gemini APIs (`gemini-3-flash` for Triage/Tier 1/Tier 2; `gemini-3.1-pro-preview` for Checker/Tier 3).
* **Rule (System Prompts):** Scraper and Ingestion agents MUST be explicitly instructed: *"You must convert any extracted Imperial or non-standard metric units into SI standard units (Nm, mm, V) before formatting your JSON output."*
* **Why:** Sandboxing isolates tool debugging from agent routing. System-level instruction acts as the first line of defense for data normalization.
* **Testing Protocol (QA Gate 5):**
    * **Sandbox Black Box:** Test Octopart API/SQLite query (`test_tier1.py`), Firecrawl scraper (`test_tier2.py`), and PDF extraction (`test_tier3.py`).
    * **White Box:** Verify SDK tool-binding syntax, strict model assignment (Pro exclusively for math/PDFs), and SQLAlchemy `INSERT` logic within the Checker agent for caching validated parts.

### Step 6: UI/Frontend Development (Dashboard & Dropzone)
* **Goal:** Build the React UI, including the Command Center (with PDF drag-and-drop zone), the dynamic Trace Waterfall, and the Live Inspector panels.
* **Why:** Translates raw SSE data packets into a visual developer-focused tuning interface, clearly indicating the data source (Tier 1 vs Tier 2).
* **Testing Protocol (QA Gate 6):**
    * **Black Box:** Dragging a PDF triggers the ingestion success state. Running a text prompt populates the waterfall iteratively. Clicking a node opens the modal with accurate latency/token metrics.
    * **White Box:** Verify React `useEffect` hooks for the SSE connection and ensure DOM updates are localized to the new node blocks rather than full-page re-renders.

### Step 7: End-to-End Testing & Prompt Tuning
* **Goal:** Stress-test the architecture with complex, obscure hardware requests to verify the Tier 2 fallback, constraint checking, and Tier 1 caching loop.
* **Why:** Proves the system is highly reliable, cost-effective, and self-improving.
* **Testing Protocol (QA Gate 7):**
    * **Black Box:** Search for an obscure part (triggers Tier 2 -> saves to DB). Search for the exact same part immediately after (triggers Tier 1 -> instant return).
    * **White Box:** Verify the SQLite Vault contains the permanently written component with the `source_type` flagged as `DEEP_SCRAPE` and all units correctly normalized to SI standards.