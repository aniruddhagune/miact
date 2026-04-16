# MIACT Project Audit & Analysis Report

**Date:** Wednesday, 15 April 2026  
**Status:** Phase 1 (Surface Fix) Completion / Pre-Phase 2 (AI Integration)  
**Stack:** FastAPI (Backend), React/Vite (Frontend), PostgreSQL (Database), spaCy/VADER (NLP)

---

## 1. Executive Summary
The MIACT (Multi-source Information Aggregator & Comparison Tool) project is a well-structured, modern web application. It features advanced search orchestration, intelligent caching, and specialized domain handling (e.g., distinguishing between technical product specs and general news). While the project demonstrates strong architectural foundations and is highly functional, it requires improvements in security (environment configuration), NLP resilience (moving beyond heuristics), and formal development practices (CI/CD).

---

## 2. Facet Scores & Analysis

### Software Engineering Practices: 7/10
*   **Strengths:** Highly modular architecture with clear separation of concerns (routes, services, extractors, nlp). Excellent use of asynchronous patterns in FastAPI for concurrent scraping.
*   **Weaknesses:** Lack of environmental configuration (hardcoded DB credentials in `backend/database/connection.py`). Documentation drift (Synopsis references outdated Streamlit tech).

### Technology Stack: 8/10
*   **Strengths:** Modern and appropriate choices (FastAPI, React/Vite, PostgreSQL, spaCy). Effective use of Server-Sent Events (SSE) for a "live" user experience.
*   **Weaknesses:** Reliance on traditional scraping which is prone to blocking; heuristic-based NLP is brittle compared to modern LLM-based extraction.

### Working State: 9/10
*   **Strengths:** Highly functional search orchestration and robust caching layer. Successful implementation of "Snippet Fallback" logic for resilient data retrieval.
*   **Weaknesses:** Inherent fragility of DOM-specific scrapers (Wikipedia, GSMArena) which break on layout changes.

### Development Methodology: 7/10
*   **Strengths:** Clear iterative evolution visible through `CONVERSATIONS.md` and `Synopsis.md`. Visible improvements in handling tech jargon and cache management.
*   **Weaknesses:** Absence of automated CI/CD pipelines, containerization (Docker), or formal automated deployment scripts.

### Project Management: 6/10
*   **Strengths:** Consistent tracking of session history and major architectural shifts in markdown files.
*   **Weaknesses:** Informal task tracking and lack of structured milestones or issue management (e.g., GitHub Issues/Jira).

---

## 3. Current State of the Project
The project successfully distinguishes between technical product specifications and general informational queries. The UI is premium, responsive, and utilizes dynamic groups for data visualization. The backend effectively orchestrates scraping, caching, and basic NLP processing.

---

## 4. Key Problems Identified
1.  **Security Vulnerability (Critical):** Plaintext database credentials hardcoded in `backend/database/connection.py`.
2.  **Heuristic Fragility:** NLP logic (`analyzer_sentiment.py`, `objectivity_classifier.py`) relies on hardcoded regex and word lists, which fail to capture linguistic nuance.
3.  **Extraction Limits:** Scrapers are tightly coupled to specific HTML patterns, making them high-maintenance.
4.  **Configuration Drift:** Potential desynchronization between frontend UI groups and backend domain logic.

---

## 5. Roadmap for Improvement

### Phase A: Immediate Technical Debt (High Priority)
*   **Environment Variables:** Move all secrets and configurations (DB URI, API keys) to a `.env` file using `python-dotenv` or Pydantic Settings.
*   **Documentation Alignment:** Synchronize `Synopsis.md` and `README.md` with the current React/FastAPI reality.
*   **Security Audit:** Ensure no sensitive information is leaked in logs or SSE streams.

### Phase B: Architecture & Resilience (Medium Term)
*   **Advanced Scraping:** Incorporate `playwright` or `trafilatura` for more resilient, headless scraping of dynamic or protected sites.
*   **Unified Config:** Create a shared configuration schema for domains/groups used by both Backend and Frontend.
*   **Automated Testing:** Implement a CI pipeline (e.g., GitHub Actions) to run the `pytest` suite on every push.

### Phase C: Hybrid AI Integration (Long Term)
*   **Ollama/LLM Integration:** Replace heuristic sentiment and entity extraction with a local LLM (e.g., Llama 3 or TinyLlama) for superior accuracy.
*   **Conflict Resolution Engine:** Develop a dedicated service to programmatically detect and flag numerical or factual discrepancies between multiple sources.
*   **Enhanced Entity Resolution:** Improve the ability to match products/entities across different naming conventions used by various sites.
