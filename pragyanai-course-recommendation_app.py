import streamlit as st
import json
import time
import os  # Import os to set the environment variable
from agents import get_course_scraper, get_course_analyst, get_recommendation_agent
from tools import get_scrape_tool

# --- NEW RAG IMPORTS ---
# We need these to create and query an in-memory vector database
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
# --- END NEW RAG IMPORTS ---

st.set_page_config(page_title="PragyanAI Course Agent", layout="wide")

# --- Header ---
st.title("PragyanAI Course Recommendation Agent 🤖")
st.markdown("This app uses a team of SmolAgents to recommend courses based on your preferences.")
st.markdown("---")

# --- User Inputs ---
col1, col2 = st.columns(2)
with col1:
    url = st.text_input("Enter the URL of the course page to scrape:", "https://www.pragyanai.school/courses")
with col2:
    user_preferences = st.text_input("Enter your course preferences:", "I'm interested in AI and Data Science.")

# --- API Key Input ---
st.sidebar.title("Configuration")
api_key = st.sidebar.text_input("Enter your API Key (Groq or other):", type="password")

if 'API_KEY_SET' not in st.session_state:
    st.session_state.API_KEY_SET = False

if api_key:
    # Set the API key for all agents in this session
    # This key will be found by the get_model() function in agents.py
    os.environ["GROQ_API_KEY"] = api_key
    
    # Also set other keys to be safe (LiteLLM checks many)
    os.environ["TOGETHER_API_KEY"] = api_key
    os.environ["HF_TOKEN"] = api_key
    os.environ["OPENAI_API_KEY"] = api_key # Just in case
    
    st.session_state.API_KEY_SET = True


# --- Main Execution ---
if st.button("Find Courses"):
    if not st.session_state.API_KEY_SET:
        st.error("Please enter your API Key in the sidebar.")
    else:
        st.info("Starting the agentic workflow... This may take a moment.")
        
        try:
            # Initialize Agents and Tools
            with st.spinner("Initializing agents and tools..."):
                scrape_tool = get_scrape_tool()
                scraper_agent = get_course_scraper(scrape_tool)
                analyst_agent = get_course_analyst()
                recommender_agent = get_recommendation_agent()

            # --- Step 1: Scrape Website (No Change) ---
            with st.spinner("Step 1/4: Scraper Agent is reading the website..."):
                scraper_prompt = f"Scrape the website at this URL: {url}"
                scraped_data = scraper_agent.run(scraper_prompt)
                
                if "Error: HYPERBROWSER_API_KEY" in scraped_data:
                    st.error("Hyperbrowser API Key is not set. Please set the HYPERBROWSER_API_KEY environment variable.")
                    raise Exception("Hyperbrowser API Key missing.")
                    
            st.success("Step 1/4: Scraping complete.")

            # --- STEP 2: RAG Pipeline (Chunk, Embed, Search) ---
            
            # 2a. Chunk the data
            with st.spinner("Step 2/4: Chunking and embedding text..."):
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
                chunks = text_splitter.split_text(scraped_data)
                
                # 2b. Initialize Embeddings & Create Vector DB
                # This uses a free, local model to create embeddings
                embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
                
                # This creates an in-memory vector database
                vector_store = FAISS.from_texts(chunks, embeddings)
                st.success(f"Step 2/4: Created vector database with {len(chunks)} chunks.")

            # 2c. Search for relevant chunks
            with st.spinner(f"Step 3/4: Searching for chunks relevant to: '{user_preferences}'..."):
                # Find the top 5 chunks that match the user's query
                relevant_chunks = vector_store.similarity_search(user_preferences, k=5)
                st.success(f"Step 3/4: Found {len(relevant_chunks)} relevant text chunks.")

            # 2d. Analyze ONLY the relevant chunks
            with st.spinner(f"Step 3/4: Analyst Agent is processing {len(relevant_chunks)} chunks..."):
                all_courses = []
                
                for i, chunk in enumerate(relevant_chunks):
                    st.write(f"Analyzing chunk {i+1}/{len(relevant_chunks)}...")
                    
                    # Define the prompt for the analyst agent
                    analyst_prompt = f"""
                    Analyze the following raw website text and extract a list of courses.
                    For each course, extract the 'title', 'description', and 'url' (if available).
                    Return the result as a clean JSON list. If no courses are found, return an empty list [].

                    Here is the JSON schema to follow:
                    [
                      {{
                        "title": "Course Title",
                        "description": "Course description.",
                        "url": "https://example.com/course-url"
                      }}
                    ]

                    Raw Text:
                    "{chunk.page_content}"
                    """
                    
                    try:
                        # Call the agent
                        chunk_result = analyst_agent.run(analyst_prompt)
                        
                        # Parse the JSON result from the agent
                        courses = json.loads(chunk_result)
                        if courses:
                            all_courses.extend(courses)
                        
                        # Add a small delay to respect rate limits, even though we're processing fewer chunks
                        time.sleep(1) 
                        
                    except json.JSONDecodeError:
                        st.error(f"Error: Analyst agent returned invalid JSON for chunk {i+1}.")
                        st.write("Agent output:", chunk_result)
                    except Exception as e:
                        st.error(f"Error processing chunk {i+1}: {e}")
                        # Stop processing if one chunk fails
                        raise
                        
                st.success(f"Step 3/4: Analysis complete. Found {len(all_courses)} relevant courses.")


            # --- Step 3: Get Recommendation ---
            if not all_courses:
                st.warning("No relevant courses were found based on your preferences.")
            else:
                with st.spinner("Step 4/4: Recommendation Agent is preparing your advice..."):
                    # Convert course list back to JSON string for the agent
                    courses_json = json.dumps(all_courses, indent=2)
                    
                    recommender_prompt = f"""
                    You are a helpful and friendly course advisor.
                    Based on the user's preferences and this list of relevant courses, 
                    provide a recommendation.

                    User Preferences: "{user_preferences}"

                    Available Courses:
                    {courses_json}

                    Please format your answer in friendly markdown.
                    Start with a summary, then list 1-3 of the *most* relevant courses 
                    with their title and description.
                    """
                    
                    recommendation = recommender_agent.run(recommender_prompt)

                st.success("Step 4/4: Recommendation generated!")
                st.markdown("---")
                st.header("Your Course Recommendation")
                st.markdown(recommendation)

        except Exception as e:
            st.error(f"An error occurred during the agent workflow:\n{e}")

