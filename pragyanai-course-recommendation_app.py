import streamlit as st
from agents import get_course_scraper, get_course_analyst, get_recommendation_agent
from tools import get_scrape_tool
import os

st.set_page_config(layout="wide")

# App title
st.title("🤖 PragyanAI Course Recommendation Agent")
st.markdown("This app uses a team of SmolAgents to recommend courses based on your preferences.")

# --- Sidebar for Inputs ---
with st.sidebar:
    st.header("1. Configuration")
    # Get Groq API key
    groq_api_key = st.text_input("Enter your Groq API Key", type="password")
    
    if not groq_api_key:
        st.warning("Please enter your Groq API key to begin.")
        st.stop()
        
    # Set the API key in the environment for LiteLLM (used by SmolAgents)
    os.environ["GROQ_API_KEY"] = groq_api_key

    st.header("2. Course Source")
    course_url = st.text_input(
        "Course Website URL", 
        "https://www.pragyanai.school/courses"
    )

    st.header("3. Your Preferences")
    user_preferences = st.text_area(
        "What are you looking for in a course?",
        "I am a beginner interested in learning about Data Science and Machine Learning. I want a course that is project-based."
    )

    get_recommendations = st.button("🚀 Get Recommendations")

# --- Main App Body for Outputs ---
if get_recommendations:
    if not course_url or not user_preferences:
        st.error("Please fill in all the fields in the sidebar.")
    else:
        try:
            # Initialize Agents and Tools
            # We re-initialize them on each run to ensure the API key is set
            scrape_tool = get_scrape_tool()
            scraper_agent = get_course_scraper(scrape_tool)
            analyst_agent = get_course_analyst()
            recommender_agent = get_recommendation_agent()

            st.info("Starting the agentic workflow... This may take a moment.")
            
            # --- Agent Workflow ---
            
            # 1. Scraper Agent
            with st.spinner("Step 1/3: 🕵️ Agent 'Course Scraper' is scraping the website..."):
                scraper_prompt = f"Scrape the website at the URL '{course_url}' to get all its text content. Return only the raw text."
                scraped_data = scraper_agent.run(scraper_prompt)
            st.success("Step 1/3: Scraping complete.")

            # 2. Analyst Agent
            with st.spinner("Step 2/3: 🧑‍🔬 Agent 'Course Analyst' is extracting structured data..."):
                analyst_prompt = f"""
                Analyze the following raw website text and extract a list of courses. 
                For each course, extract the 'title', 'description', and 'url' (if available).
                Return the result as a clean JSON list.
                
                Example Output:
                [
                  {{
                    "title": "Introduction to Python",
                    "description": "A beginner-friendly course on Python.",
                    "url": "/courses/python"
                  }}
                ]
                
                Raw Text:
                {scraped_data}
                """
                structured_data = analyst_agent.run(analyst_prompt)
            st.success("Step 2/3: Analysis complete.")
            
            # Display the structured data
            with st.expander("See extracted course data (JSON)"):
                st.json(structured_data)

            # 3. Recommendation Agent
            with st.spinner("Step 3/3: 🤖 Agent 'Recommender' is generating personalized advice..."):
                recommender_prompt = f"""
                You are a friendly and expert course advisor. 
                Based on the following user preferences and the list of available courses (in JSON format), 
                provide a helpful recommendation.
                
                Address the user directly. Explain WHY you are recommending 1-3 specific courses, 
                connecting them directly to the user's stated preferences.
                
                User Preferences:
                "{user_preferences}"
                
                Available Courses (JSON):
                {structured_data}
                
                Return your recommendation as a well-formatted Markdown text.
                """
                recommendations = recommender_agent.run(recommender_prompt)
            st.success("Step 3/3: Recommendations generated!")

            # --- Final Output ---
            st.divider()
            st.header("✨ Your Personalized Course Recommendations")
            st.markdown(recommendations)
            
        except Exception as e:
            st.error(f"An error occurred during the agent workflow:")
            st.exception(e)

else:
    st.info("Please fill in your API key and preferences in the sidebar to get started.")

