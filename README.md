# MIACT: Multi-source Information Aggregator & Comparison Tool

MIACT is a locally executable, lightweight data aggregation and analysis tool designed to fetch, compare, and summarize information from multiple web sources using asynchronous scraping and Natural Language Processing (NLP) techniques.

## 🚀 Aim
To reduce research fatigue by providing a consolidated view of objective facts and subjective opinions on products and news topics, highlighting conflicting claims across different sources.

## 🛠️ Tech Stack
- **Frontend:** React (Vite) with Lucide Icons and Tailwind-inspired styling.
- **Backend:** FastAPI (Python) for high-performance asynchronous orchestration.
- **Database:** PostgreSQL for persistent local caching.
- **NLP:** spaCy (Dependency Parsing) and VADER (Sentiment Analysis).
- **Scraping:** Requests, BeautifulSoup, and Newspaper3k.

## 📦 Core Features
- **Intelligent Domain Handling:** Specialized pipelines for Consumer Electronics (Phones/Laptops) and News.
- **Fact Cascade:** Automatically queries trusted domains like GSMArena and Wikipedia for structured specifications.
- **Sentiment Mapping:** Extracts and groups subjective opinions by canonical aspects (e.g., "Battery", "Camera").
- **Local Cache:** Stores results in PostgreSQL to ensure fast retrieval for repeated queries.
- **Real-time Updates:** Uses Server-Sent Events (SSE) to show extraction progress in the UI.
- **Debug Mode:** Detailed session logging and server-side event tracking.

## 🔧 Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js & npm
- PostgreSQL

### Backend Setup
1. Navigate to the `backend` directory.
2. Create a virtual environment: `python -m venv venv`.
3. Activate the environment and install dependencies: `pip install -r requirements.txt`.
4. Install the spaCy model: `python -m spacy download en_core_web_md`.
5. Configure your database credentials in a `.env` file in the root directory (see `.env.example`).

### Frontend Setup
1. Navigate to the `frontend` directory.
2. Install dependencies: `npm install`.
3. Start the development server: `npm run dev`.

## 📂 Project Structure
- `backend/`: FastAPI application, NLP logic, and database services.
- `frontend/`: React application and UI components.
- `debug/`: Session-specific logs (created at runtime).
- `diagrams/`: Architectural and class diagrams.

## 🛡️ Security Note
MIACT is designed for local use. Database credentials and environment variables are managed through `.env` files. Ensure your local PostgreSQL instance is secured.
