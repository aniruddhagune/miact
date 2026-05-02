# MIACT: Queries & Workspace

This file is used for detailed queries and in-depth discussions. 

### How to use:
1. **User:** Post your detailed query/problem under the "Active Queries" section.
2. **Gemini:** I will provide a detailed answer/proposal below your query.
3. **Refinement:** we can iterate here until the solution is finalized.
4. **Finalization:** Once resolved, I will move the summary to `CONVERSATIONS.md`.

---

## Done Queries

### Topic: Upgrading NLP while maintaining "Lightweight" status

**User Concern:** Overall project size and processing cost. The goal is a locally executable and light project.

**Gemini's Analysis:**
Adding a large LLM (5GB+) would violate the "lightweight" goal. However, we can achieve better results using a **Hybrid AI Strategy**:

1. **The "Tiny" Model:** Instead of Llama 3 (5GB), use **TinyLlama-1.1B** (~600MB). It is fast enough to run on basic CPUs and small enough to be considered "light."
2. **Conditional Logic (Fallbacks):** The app should not *require* the LLM. 
   - *Logic:* `if ollama_running(): use_tinyllama() else: use_regex_heuristics()`
   - This keeps the core app size tiny while allowing users to "power up" if they choose.
3. **Selective Use:** Don't use AI to find "8GB RAM" (regex is better/faster). Only use AI to:
   - Summarize 50+ user comments into 3 key pros/cons.
   - Explain why two news sources have conflicting dates.

**Proposed Plan:**
- **Phase 1:** (COMPLETED) Implement Database Caching.
- **Phase 2:** Create a "Lightweight LLM Service" that handles complex tasks only when needed (Heuristics vs. LLM branch strategy).

**Next Step:**
Phase 1 is complete! We have addressed several "surface issues," but two major ones remain for our next session.

---

## Non - Active Queries (Next Session Roadmap)

### 1. Fix: Blank Results for Specific Subjects (e.g., "Indian Tax Act")
**Problem:** The "Snippet Fallback" was implemented for News but not yet for Entity searches. If Wikipedia blocks the request, the result stays blank.
**Plan:** 
- [ ] Update the Entity loop in `search.py` to pass search snippets as fallback text.
- [ ] Verify that the `query_type` detection doesn't accidentally filter out general topics.

### 2. Solution: Robust Scraping for Blocked Sites
**Problem:** Basic BeautifulSoup scraping is easily blocked by sites with high traffic or anti-bot measures.
**Plan:**
- [ ] **Wikipedia API Integration:** Use the official Wikipedia API (Action API) to fetch data. It is faster, structured, and never blocked.
- [ ] **Trafilatura/Playwright:** Research integrating `trafilatura` for generic sites or using the existing `playwright` setup for sites that require JavaScript.

### 3. Subject Extraction Refinement
**Problem:** Non-tech subjects may be misidentified or stripped by the current logic.
**Plan:**
- [ ] Update `detector_subjects.py` to be less "tech-centric" when the query is identified as general.


### USER 

About the plan, **Phase 1** sounds good. 
About **Phase 2**, I would suggest to proceed with both the methods, one by one. LLM in other branch and Heuristics in another branch. 
Let's decide and sort this, then I have many other issues to address, visibly up on the surface.

### 1. Issue: Tech Jargon in Non-Tech Searches & Missing Results for General Topics
**Status:** **IN PROGRESS (Core Fixes Applied)**

**Root Causes Identified:**
1. **Fact Cascade Leakage:** The system was explicitly searching `gsmarena.com` and `devicespecifications.com` even for non-tech queries like "Mahatma Gandhi." If any results were found, the tech-specific scrapers would extract jargon and attribute it to the person.
2. **Aggressive Tech Patterns:** `extract_attributes` was applying tech-heavy regex (e.g., for battery, storage) to every piece of text it found, regardless of the topic.
3. **News Mode Snippets:** "Indian Tax Act" showed nothing because the system was returning raw search snippets which the frontend doesn't know how to display.
4. **Tech-Biased Sentiment:** The sentiment lexicon is heavily weighted toward product reviews (e.g., "snappy", "vivid").

**Fixes Implemented:**
- [x] **Domain-Aware Search:** Modified `search.py` to only use tech domains for tech queries. For news and general topics, it now only uses Wikipedia as a factual source.
- [x] **Pipeline for News:** News and General topics are now processed through the full `process_query_url` pipeline, ensuring we get structured facts (like dates) and opinions instead of empty snippets.
- [x] **Extraction Guard:** Added a "Domain Guard" to `extract_attributes` so tech patterns are only triggered if the query is identified as "tech_phone" or "tech_laptop".

**Remaining Tasks:**
- [ ] **De-bias Sentiment:** Refine the sentiment lexicon to distinguish between "product" sentiment and "general" sentiment.
- [ ] **Dynamic UI Labels:** (Optional) Adjust the frontend to use more appropriate headers than "FACTS" for non-tech subjects.

**Next Question for User:**
I have applied the core fixes to the backend. Would you like to test these changes by searching for "Mahatma Gandhi" or "Indian Tax Act" again to see the improvement? Or should I proceed with de-biasing the sentiment logic?

## Active Queries

1. Create a new branch on git, and update this version of project on the new branch of current github repository. Name of new branch will be "d-work"

2. We do need a Debug mode and button, which can help us track and know everything going on in the server. Which sites are working, which are giving errors, and what else is happeing on the background. And also, all this debug information is coming up, it will be stored in a file which is created for each session, in a debug folder. How we can setup the debug and what will be available in debug mode.


--------------------------------------

