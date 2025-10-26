from smolagents import CodeAgent, LiteLLMModel

def get_model(model_name="groq/meta-llama/llama-4-maverick-17b-128e-instruct"):
    """Initializes the LiteLLMModel to connect to Groq."""
    # LiteLLMModel can call any provider LiteLLM supports, including Groq.
    # It automatically looks for the "GROQ_API_KEY" environment variable.
    return LiteLLMModel(model_id=model_name)

def get_course_scraper(scrape_tool):
    """
    Returns a SmolAgent responsible for scraping websites.
    It has access to the scraping tool.
    """
    return CodeAgent(
        name="Course_Scraper",
        model=get_model(),
        description="This agent is an expert at scraping website content using the provided tools.",
        tools=[scrape_tool]
    )

def get_course_analyst():
    """
    Returns a SmolAgent responsible for analyzing text and extracting structured data.
    """
    return CodeAgent(
        name="Course_Analyst",
        model=get_model(model_name="groq/meta-llama/llama-4-maverick-17b-128e-instruct"), # Use a stronger model for JSON extraction
        description="This agent is an expert at reading raw text and converting it into structured JSON data.",
        tools=[] # This agent doesn't need external tools
    )

def get_recommendation_agent():
    """
    Returns a SmolAgent responsible for providing personalized recommendations.
    """
    return CodeAgent(
        name="Recommendation_Agent",
        model=get_model(),
        description="This agent is an expert at comparing user preferences with a list of courses to provide helpful advice.",
        tools=[] # This agent doesn't need external tools
    )
