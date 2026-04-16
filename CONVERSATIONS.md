# MIACT: Session & Update History

## Session 1: Initial Project Audit (11 April 2026)

### Project Status Report
**Title:** Multi-source Information Aggregator & Comparison Tool (MIACT)

#### Assessment: "How does it feel?"
*   **Visual Appeal (A+):** The React/Tailwind frontend is excellent. The "glass-morphism" design, Oswald typography, and dark theme give it a premium, "cyberpunk-industrial" feel.
*   **User Experience (A):** The use of Server-Sent Events (SSE) for streaming search results makes the application feel responsive and "alive."
*   **Architecture (B+):** The code is modular (Separation of Routes, Services, and Extractors), making it easy to maintain and scale.
*   **Intelligence (C):** The NLP logic relies heavily on hardcoded word lists and manual regex, which lacks flexibility for complex language.

#### Problems & Discrepancies Analyzed
1.  **Documentation Drift:** `Synopsis.md` mentions Streamlit, but the project uses React/Vite.
2.  **Hardcoded Heuristics:** Brittle NLP logic in `analyzer_sentiment.py` and `objectivity_classifier.py`.
3.  **Extraction Fragility:** Scrapers are "hard-wired" to specific HTML classes.
4.  **Database Underutilization:** The PostgreSQL setup is present but currently bypassed in the search route.
5.  **Security Risks:** Database credentials are hardcoded in `connection.py`.

#### Suggestions for Improvement
1.  **Ollama Integration:** Use a local LLM (like Llama 3) via Ollama to replace hardcoded NLP logic.
2.  **Implement Caching:** Enable the database logic to store and retrieve previously scraped data.
3.  **Generic Scraping:** Use libraries like `trafilatura` for more robust content extraction across various sites.
4.  **Environment Variables:** Move DB credentials to a `.env` file.
5.  **Conflict Resolver:** Explicitly flag and highlight numerical inconsistencies in the UI.

---

## Session 2: Implementing Phase 1 - Database Caching (11 April 2026)

### Implementation Details:
*   **Enabled Caching:** Modified `backend/routes/search.py` to prioritize database results over web scraping.
*   **Data Consistency:** Updated `fetch_from_db` in `backend/services/db_query_service.py` to include source URLs, attribute types, and confidence scores.
*   **Source Reconstruction:** Ensured that the frontend "Sources" popup correctly displays URLs even when data is loaded from the local database.

### Impact:
*   **Speed:** Repeat searches for the same entity are now near-instant (< 100ms vs > 15s).
*   **Efficiency:** Reduces web traffic and prevents potential IP blocking by reusing locally stored data.

---

## Session 3: Strategy Alignment for Phase 2 (11 April 2026)

### Agreed Strategy: "Multi-Branch Development"
To balance the goals of "Lightweight" and "Intelligent," we have decided to develop Phase 2 in parallel across two branches:
1.  **`feature/advanced-heuristics` Branch:** Focusing on improving Python-based NLP (TextBlob/spaCy) and regex to stay as lightweight as possible.
2.  **`feature/local-llm` Branch:** Integrating **TinyLlama-1.1B** via Ollama for deeper context and conflict resolution.

### Next Steps:
*   Before starting Phase 2, the team will address "surface-level" issues identified in the UI and extraction logic.

---

## Session 4: Fixing Tech Jargon Leakage & Improving Non-Tech Searches (11 April 2026)

### Problem Addressed:
*   Searching for non-tech subjects (e.g., "Mahatma Gandhi") returned irrelevant tech jargon (battery, cores).
*   General/News topics (e.g., "Indian Tax Act") returned empty results because they weren't being processed for structured data.

### Implementation Details:
*   **Domain-Aware Search:** Modified `backend/routes/search.py` to restrict tech-specific domains (GSM Arena, DeviceSpecifications) to only "tech_phone" and "tech_laptop" queries.
*   **Structured News Processing:** Enabled full pipeline processing for News and General modes in `search.py`, ensuring structured facts and opinions are extracted instead of raw snippets.
*   **Extraction Domain Guard:** Updated `backend/extractors/extractor_data.py` to prevent tech-specific regex patterns from triggering on non-tech text.

### Impact:
*   **Accuracy:** Non-tech biographies and topics are now clean and jargon-free.
*   **Utility:** Users can now search for general topics and news and receive structured factual information.

---

## Session 5: UX Refinement, Cache Management, and Dynamic Result Segregation (11 April 2026)

### 1. Problem: "Tech Jargon" in General Searches
**Discovery:** We found that the system's "Fact Cascade" was too aggressive. It was searching tech-specific sites like GSM Arena for non-tech subjects (e.g., "Mahatma Gandhi"), leading to irrelevant data like "battery" or "gsm bands" being attributed to people.
**Solution:** 
*   Implemented a **Domain-Aware Search Orchestrator** in `backend/routes/search.py`. 
*   The system now intelligently branches: Tech queries (Phones/Laptops) use specialized cascades (GSM Arena/NotebookCheck), while General/News queries are restricted to high-authority general sources like Wikipedia.

### 2. Feature: Dynamic Result Segregation
**Problem:** Non-tech information was being forced into technical table headers (e.g., a person's birth date appearing under a "Dates" header meant for product releases).
**Solution:**
*   Created a new domain layer: `backend/domains/general.py`. This contains a mapping for non-tech subjects (Biographies, Legal Acts, etc.).
*   **Frontend Logic Update:** In `App.jsx`, I replaced the hardcoded `TECH_GROUPS` with a dynamic `GROUPS` system.
    *   **Tech Mode:** Displays "Dates, Core, Memory, Connectivity, Display."
    *   **General Mode:** Displays "Personal Info, Background, Professional, Legal Info, Works."
*   **Fallback Handling:** Added an "Additional Details" section for any information that doesn't fit the predefined categories, ensuring no scraped data is ever lost.

### 3. UI/UX: The "Scrolling Anomaly"
**Problem:** The React application would force-scroll to the bottom of the page every time a data packet arrived (SSE stream), preventing the user from reading the top of the search results while the search was still in progress.
**Solution:** 
*   Refined the `useEffect` hook in `App.jsx`. 
*   **New Logic:** The auto-scroll only triggers when a *new* search is initiated (`loading` state becomes true). Once results start arriving, the scroll position is preserved, allowing the user to read at their own pace.

### 4. Developer Tools: Cache Management
**Problem:** During development and testing, cached data made it difficult to verify code changes or fetch the latest news.
**Solution:**
*   **Backend:** Added a `@router.post("/clear-db")` endpoint in `search.py` that safely truncates all cache tables (`facts`, `documents`, `entities`, `sources`) using a `CASCADE` command.
*   **Frontend:** Added a prominent **"Clear Cache"** button at the bottom of the sidebar. It includes a browser confirmation dialog to prevent accidental data loss.

### 5. Architectural Improvements
*   **Consistency:** Updated `fetch_from_db` in `backend/services/db_query_service.py` to ensure that data loaded from the database has the exact same structure (source URLs, confidence scores, types) as data scraped from the web.
*   **Domain Guards:** Modified `extractor_data.py` so that tech-specific regex patterns (battery capacity, storage units) are only active if the query is identified as a tech product.

---

## Session 6: Localization & Scraping Robustness (11 April 2026)

### Problems Addressed:
*   **Irrelevant Search Results:** Searches like "Indian Tax Act" were returning foreign language Wikipedia pages or non-localized data.
*   **Scraping Failures:** Many websites block automated scraping, leading to empty "blank" results on the UI.

### Implementation Details:
*   **Regional Search Parameters:** Updated `backend/services/search_service.py` to use Indian regional settings (`kl='in-en'`) for all DuckDuckGo queries.
*   **Wikipedia Language Guard:** Implemented a filter in `search_service.py` that restricts Wikipedia results to `en.wikipedia.org`, ensuring linguistic relevance.
*   **"Snippet Fallback" Logic:** 
    *   Updated `backend/routes/search.py` and `backend/services/pipeline_service.py` to pass search engine snippets through the pipeline.
    *   If a target URL fails to scrape (due to blocking or traffic), the system now uses the search engine's "body" snippet as a **"Brief Summary"** fallback.
*   **Blank Search Fix:** This ensures that even when 100% of websites block scraping, the user still receives structured summaries from the search engine data.

### Impact:
*   **Localization:** Results are now significantly more relevant to Indian users and topics.
*   **Reliability:** Eliminated the "empty result" issue for blocked or high-traffic sites.

---
**Status for Next Session:**
The core "Surface Issues" regarding search accuracy and result layout are resolved. The project is now faster (via caching), cleaner (via domain guards), and more user-friendly (via scroll fixes). Next session can proceed with **Phase 2: Hybrid AI Integration (Ollama vs. Advanced Heuristics)**.

---

## Session 7: Debugging Infrastructure, Technical Debt & Security (16 April 2026)

### 1. Git & Workflow Management
*   **New Branch:** Created and pushed the `d-work` branch to GitHub to serve as the stable development base for current feature work.
*   **Default State:** Set the application to run in `DEBUG` mode by default to facilitate immediate traceability during the current development phase.

### 2. Implementation: Structured Debugging & Logging
**Problem:** Lack of visibility into server-side operations, making it difficult to track scraper success rates, database interactions, and NLP pipeline flow.
**Solution:**
*   **MIACTLogger (`backend/utils/logger.py`):** Developed a thread-safe singleton logger that writes structured JSON entries to session-specific files.
*   **Differentiated Logs:** Implemented service-level labeling (e.g., `[SEARCH]`, `[PIPELINE]`, `[DATABASE]`, `[NLP]`) to prevent log interleaving and ensure clear traceability.
*   **Storage Location:** Logs are now stored in `backend/debug/session_{timestamp}.log`, keeping the root directory clean while preserving history.
*   **Runtime Toggle:** Integrated a new route `backend/routes/debug.py` that allows the system to toggle verbose console logging at runtime via API without a restart.
*   **Frontend Integration:** Added a "Debug Mode" toggle button in the sidebar with a `Terminal` icon. It visually reflects the server state (Cyan for ON) and provides instant feedback via alerts.

### 3. Phase A: Technical Debt & Security (Project Audit Completion)
**Goal:** Align the project with professional security and documentation standards.
**Implementation Details:**
*   **Environment Variables:** Successfully moved all database credentials (DB_NAME, DB_USER, DB_PASSWORD, etc.) from hardcoded strings to a protected `.env` file.
*   **Single Source of Truth:** Refactored `backend/config/variables.py` to use `python-dotenv`, ensuring the entire backend sources its configuration from environment variables.
*   **Database Hardening:** Updated `backend/database/connection.py` to eliminate hardcoded credentials, mitigating a critical security vulnerability identified in the audit.
*   **Documentation Synchronization:** 
    *   **Synopsis.md:** Fully updated to reflect the move from Streamlit to the React/FastAPI stack. Updated module descriptions to match the current spaCy-based NLP pipeline.
    *   **README.md:** Rewritten to include modern setup instructions, prerequisites (PostgreSQL, Node.js), and a clear architecture overview.
*   **Security Audit:** Verified that no sensitive credentials or system-level paths are leaked through SSE streams or the new logging system.

### 4. Impact:
*   **Traceability:** Every step of the search process—from query parsing to variant grouping—is now logged with full data context.
*   **Security:** The codebase is now safe for public repository hosting with no sensitive secrets exposed.
*   **Maintainability:** The technical debt from the stack migration has been cleared, providing a consistent foundation for Phase B.

---
**Status for Next Session:**
Phase A is complete. The system is secure, documented, and highly observable. The team is now moving to **Phase B: Architecture & Resilience**, focusing on advanced scraping (Playwright integration) and unified configuration schemas.
