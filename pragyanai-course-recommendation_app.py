import streamlit as st
import os
import json  # <-- Import JSON for parsing
from agents import get_course_scraper, get_course_analyst, get_recommendation_agent
from tools import get_scrape_tool
# --- FIX: Import Text Splitter ---
from langchain.text_splitter import RecursiveCharacterTextSplitter

# --- Page Config ---
st.set_page_config(
    page_title="PragyanAI Course Agent",
    page_icon="🤖",
    layout="wide"
)

# --- Header ---
st.title("🤖 PragyanAI Course Recommendation Agent")
st.markdown("""
This app uses a team of **SmolAgents** to recommend courses based on your preferences.
Enter a URL of a course catalog and your learning goals, and the agents will do the rest!
""")

# --- API Key Management ---
st.sidebar.header("🔑 API Keys")
st.sidebar.markdown("""
You need API keys for the services this app uses:
1.  **Groq API Key**: For the AI models.
2.  **Hyperbrowser API Key**: For web scraping.
""")

groq_api_key = st.sidebar.text_input("Groq API Key (GROQ_API_KEY)", type="password")
hyperbrowser_api_key = st.sidebar.text_input("Hyperbrowser API Key (HYPERBROWSER_API_KEY)", type="password")

if groq_api_key:
    os.environ["GROQ_API_KEY"] = groq_api_key
if hyperbrowser_api_key:
    os.environ["HYPERBROWSER_API_KEY"] = hyperbrowser_api_key

# --- User Input ---
st.header("1. Define Your Search")
course_url = st.text_input(
    "Enter the URL of the course catalog:",
    "https://www.pragyanai.school/courses"
)
user_preferences = st.text_area(
    "What are your learning goals?",
    "I'm a beginner looking to get into data science. I'm interested in Python, pandas, and basic machine learning."
)

if st.button("🚀 Start Recommendation Process"):
    if not groq_api_key or not hyperbrowser_api_key:
        st.error("Please enter both Groq and Hyperbrowser API keys in the sidebar to proceed.")
    else:
        try:
            st.info("Starting the agentic workflow... This may take a moment.")
            
            # --- Initialize Agents and Tools ---
            scrape_tool = get_scrape_tool()
            scraper_agent = get_course_scraper(scrape_tool)
            analyst_agent = get_course_analyst()
            recommender_agent = get_recommendation_agent()

            # --- Agent Workflow ---
            
            # Step 1: Scrape the website
            with st.spinner("Step 1/3: The Scraper Agent is reading the website..."):
                scraper_prompt = f"Please scrape the full text content from this URL: {course_url}"
                scraped_data = scraper_agent.run(scraper_prompt)
                if scraped_data.startswith("Error:"):
                    st.error(f"Scraping failed: {scraped_data}")
                    st.stop()
            st.success("Step 1/3: Scraping complete.")

            # --- FIX: Chunk the Scraped Data ---
            st.info("Splitting scraped data into manageable chunks...")
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=8000,  # Aim for chunks smaller than the limit
                chunk_overlap=400,
                length_function=len,
            )
            text_chunks = text_splitter.split_text(scraped_data)
            st.info(f"Data split into {len(text_chunks)} chunk(s).")
            # --- END FIX ---

            # Step 2: Analyze the scraped data
            with st.spinner(f"Step 2/3: The Analyst Agent is extracting courses from {len(text_chunks)} chunk(s)..."):
                
                # --- FIX: Loop through chunks and aggregate results ---
                all_courses = []
                total_chunks = len(text_chunks)

                for i, chunk in enumerate(text_chunks):
                    st.spinner(f"Step 2/3: Analyzing chunk {i+1} of {total_chunks}...")
                    analyst_prompt = f"""
                    Analyze the following raw website text and extract a list of courses. 
                    For each course, please extract the 'title', 'description', and 'url' (if available).
                    Return the result as a clean JSON list, where each item is an object.
                    Example:
                    [
                        {{"title": "Intro to Python", "description": "Learn the basics...", "url": "/courses/python"}},
                        {{"title": "Advanced ML", "description": "Deep dive into models...", "url": "/courses/ml"}}
                    ]

                    If no courses are found in this chunk, return an empty list [].

                    Raw Text Chunk:
                    {chunk}
                    """
                    
                    try:
                        # Run agent on the chunk
                        chunk_result_str = analyst_agent.run(analyst_prompt)
                        
                        # Attempt to parse the JSON response
                        if chunk_result_str:
                            chunk_courses = json.loads(chunk_result_str)
                            if isinstance(chunk_courses, list):
                                all_courses.extend(chunk_courses)
                        
                    except json.JSONDecodeError:
                        st.warning(f"Agent returned invalid JSON for chunk {i+1}. Skipping chunk.")
                    except Exception as e:
                        st.warning(f"Error processing chunk {i+1}: {e}")
                
                # Use the aggregated list
                structured_data = json.dumps(all_courses, indent=2)
                # --- END FIX ---

                if not all_courses:
                    st.error("Analysis failed: The agent did not find any courses in the document.")
                    st.stop()
            st.success(f"Step 2/3: Analysis complete. Found {len(all_courses)} courses.")

            # Step 3: Get recommendations
            with st.spinner("Step 3/3: The Recommender Agent is preparing your recommendations..."):
                recommender_prompt = f"""
                Here is a list of available courses in JSON format:
                {structured_data} 

                Here are the user's preferences:
                "{user_preferences}"

                Please analyze the courses and the user's preferences. 
                Return a markdown-formatted response with:
                1.  A short summary of why you are recommending these courses.
                2.  A list of the top 3-5 recommended courses.
                3.  For each recommended course, include its title, description, and URL (if available).
                """
                recommendations = recommender_agent.run(recommender_prompt)
            st.success("Step 3/3: Recommendations ready!")

            # --- Display Results ---
            st.header("✅ Your Course Recommendations")
            st.markdown(recommendations)
            
            with st.expander("Show Analyzed Course Data (JSON)"):
                # Display the aggregated JSON
                st.json(structured_data)
            
            with st.expander("Show Raw Scraped Text"):
                st.text(scraped_data)

        except Exception as e:
            st.error(f"An error occurred during the agent workflow:\n{e}")
            st.exception(e)



