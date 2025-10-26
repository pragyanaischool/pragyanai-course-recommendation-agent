Course Recommender Agent System

This project implements a multi-agent course recommendation system based on the architecture specified. It uses CrewAI for agent orchestration, Groq for low-latency LLM inference (LLaMA 3), Streamlit for the UI, and a dedicated scraping and analysis pipeline for populating the course database.

Project Structure

streamlit_app.py: The main user interface, built with Streamlit.

crew.py: Defines the main CrewAI orchestration, assembling agents and tasks.

agents.py: Defines the responsibilities and prompts for each individual agent (Intake, Skill, Price, etc.).

tools.py: Contains the Python-based tools (logic, calculations, DB lookups) that the agents use.

llm_client.py: A centralized client for interacting with the Groq API for LLaMA 3.

data_models.py: Pydantic models for Course and UserProfile to ensure structured data.

vector_store.py: A wrapper for faiss and sentence-transformers to manage course embeddings and semantic search.

scraper.py: A data scraping module using Playwright and BeautifulSoup to fetch course data.

analysis.py: A module for the "Course Analyzer" logic, using an LLM to extract structured data from raw course text.

requirements.txt: A list of all Python dependencies.

Setup

Install Dependencies:

pip install -r requirements.txt
playwright install chromium


Set Environment Variables:
Create a .env file in the root directory and add your API keys:

GROQ_API_KEY=your_groq_api_key_here
CREWAI_API_KEY=your_crewai_api_key_here


Prepare Data:

Run the scraper to generate a courses_parsed.jsonl file:

python scraper.py


Run the analysis pipeline to create structured course data (this will call the LLM):

python analysis.py


Run an indexing script (to be built) to load courses_structured.jsonl into the vector_store.

Run the App:

streamlit run streamlit_app.py


Quick Citations (Load-Bearing Sources)

As requested, here are the primary technologies and sources referenced in the design:

LLaMA 3.1 (70B) instruction-tuned model: Model card & release info (via Groq)

Groq: Low-latency inference hardware + API reference

CrewAI (CrewAI AMP): Multi-agent orchestration, visual agent builder and docs

Streamlit: UI framework

Playwright: Browser automation for scraping

SentenceTransformers: Embedding models

Faiss: Vector search library
