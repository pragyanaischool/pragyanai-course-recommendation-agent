import os
from smolagents import CodeAgent
from smolagents.models import LiteLLMModel


# --- THIS IS THE MODEL FIX ---
# We are NOW sticking to Groq's Llama 3 70b model, which has a much higher
# tokens-per-minute (TPM) rate limit. This will fix the rate limit errors.
NEW_MODEL_NAME = "groq/llama-3.1-8b-instant"
# --- END MODEL FIX ---

def get_model(model_name=NEW_MODEL_NAME):
    """
    Initializes and returns a LiteLLMModel.
    """
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable not set.")
    
    # --- THIS IS THE FIX (Applying your "add delay" suggestion) ---
    # We are telling LiteLLM to automatically retry up to 5 times
    # if it hits a RateLimitError. This will wait (with a delay) and
    # try again, which is exactly what the error message suggests.
    return LiteLLMModel(
        model_id=model_name,
        api_key=api_key,
        num_retries=5, # Automatically retry up to 5 times
        retry_strategy="exponential_backoff" # Use a delay between retries
        # --- REMOVED UNSUPPORTED PARAMETERS ---
        # The 'retry_base_backoff' and 'retry_max_backoff' parameters
        # caused the BadRequestError and have been removed.
        # --- END OF REMOVAL ---
    )
    # --- END FIX ---

def get_course_scraper(scrape_tool):
    """
    Returns a SmolAgent responsible for scraping a website.
    It is given the a scraping tool upon initialization.
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

