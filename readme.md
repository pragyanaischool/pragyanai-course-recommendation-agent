PragyanAI Course Recommendation Agent (SmolAgents Version)

This project implements a multi-agent course recommendation system using SmolAgents and Streamlit.

This is a complete, working application that replaces the incomplete CrewAI version in the original repository. It uses a team of three specialized AI agents to provide personalized course recommendations based on a user's preferences and the content of a course website.

Architecture

This application uses a sequential, multi-agent workflow:

Streamlit UI (streamlit_app.py): The user provides their Groq API key, a target URL for a course website, and their personal preferences.

Agent 1: Course Scraper (agents.py): This agent receives the URL, uses the ScrapeWebsiteTool (tools.py) to fetch the raw text content of the page, and passes it to the next agent.

Agent 2: Course Analyst (agents.py): This agent receives the raw text. Its job is to read the text, identify all the courses, and extract a structured JSON list containing each course's title, description, and url.

Agent 3: Recommendation Agent (agents.py): This agent receives the structured JSON data and the user's original preferences. Its job is to act as a friendly advisor, comparing the user's needs to the available courses and writing a personalized recommendation in Markdown.

Streamlit UI (streamlit_app.py): The final recommendation is displayed to the user.

How to Run

Get a Groq API Key:

This app uses Groq for high-speed LLM inference (Llama 3).

Sign up for a free account at https://console.groq.com/keys and create an API key.

Clone this repository and install dependencies:

git clone <your-repo-url>
cd <your-repo-name>
pip install -r requirements.txt


Run the Streamlit App:

streamlit run streamlit_app.py


Use the App:

The app will open in your browser.

Paste your Groq API key into the sidebar.

Enter the URL of the course page you want to analyze.

Write down your learning preferences.

Click "Get Recommendations" and watch the agents work!
