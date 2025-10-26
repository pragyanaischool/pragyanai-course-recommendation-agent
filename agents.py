import os
from smolagents import CodeAgent
# --- THIS IS THE FIX ---
# The import path was incorrect. LiteLLMModel is directly in smolagents.models
from smolagents.models import LiteLLMModel
# --- END FIX ---


# --- THIS IS THE NEW MODEL ---
NEW_MODEL_NAME = "groq/llama-3.1-8b-instant"
# --- END NEW MODEL ---

def get_model(model_name=NEW_MODEL_NAME):
    """
    Initializes and returns a LiteLLMModel.
    
    --- UPDATED LOGIC ---
    We no longer explicitly pass an API key.
    LiteLLMModel (via litellm) will automatically find the correct API key 
    (e.g., TOGETHER_API_KEY, HF_TOKEN, etc.) from your environment variables
    based on the model name.
    
    Make sure you have set the correct environment variable for your model provider.
    --- END UPDATE ---
    """
    
    # The api_key parameter is removed.
    # litellm will handle authentication.
    return LiteLLMModel(
        model_id=model_name,
    )

def get_course_scraper(scrape_tool):
    """
    Returns a SmolAgent responsible for scraping a website.
    It is given the scraping tool upon initialization.
    """
    
    scraper_model = get_model() # Uses the new default model
    
    return CodeAgent(
        name="Course_Scraper",
        model=scraper_model,
        description=(
            "This agent is an expert at using tools. "
            "Its job is to run the 'scrape_website_with_hyperbrowser' tool. "
            "It will be given a prompt with a URL and should just call the tool with that URL."
        ),
        tools=[scrape_tool]
    )

def get_course_analyst():
    """
    Returns a SmolAgent responsible for analyzing text and extracting structured data.
    """
    
    analyst_model = get_model() # Uses the new default model
    
    return CodeAgent(
        name="Course_Analyst",
        model=analyst_model,
        description=(
            "This agent is an expert at reading raw text and converting it into structured JSON data. "
            "It is given a JSON schema and text and MUST return only valid JSON."
        ),
        tools=[] # This agent doesn't need tools, it just processes text
    )

def get_recommendation_agent():
    """
    Returns a SmolAgent responsible for providing recommendations.
    """
    
    recommender_model = get_model() # Uses the new default model
    
    return CodeAgent(
        name="Recommendation_Agent",
        model=recommender_model,
        description=(
            "This agent is a helpful course advisor. "
            "It takes a list of courses (in JSON) and user preferences (as text) "
            "and returns a helpful, formatted markdown recommendation."
        ),
        tools=[] # This agent also just processes text
    )

