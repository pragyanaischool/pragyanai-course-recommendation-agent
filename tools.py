import os
from langchain_core.tools import tool  # <-- This import is the fix
from langchain_hyperbrowser import HyperbrowserScrapeTool

# --- MODIFICATION ---
# Load the Hyperbrowser API key from environment variables
# You MUST set this environment variable for the tool to work.
HYPERBROWSER_API_KEY = os.getenv("HYPERBROWSER_API_KEY")

# Initialize the underlying tool once to be reused
# Pass the API key during initialization
_hyperbrowser_scraper = HyperbrowserScrapeTool(api_key=HYPERBROWSER_API_KEY)
# --- END MODIFICATION ---


@tool
def scrape_website_with_hyperbrowser(url: str) -> str:
    """
    Scrapes a single website URL using Hyperbrowser and returns the content
    as Markdown. Use this tool to get the text content from a webpage.
    Input must be a single URL string.
    """

    # --- ADDED CHECK ---
    if not HYPERBROWSER_API_KEY:
        return (
            "Error: HYPERBROWSER_API_KEY environment variable is not set. "
            "This tool cannot function without an API key."
        )
    # --- END CHECK ---

    try:
        # Hyperbrowser expects a dictionary for its invoke method
        result = _hyperbrowser_scraper.invoke(
            {"url": url, "scrape_options": {"formats": ["markdown"]}}
        )

        # The tool returns a dictionary, let's grab the markdown content
        # Check if 'markdown' key exists and is not empty
        if isinstance(result, dict) and result.get("markdown"):
            return result["markdown"]
        else:
            # Fallback in case the structure is different or markdown is empty
            return str(result)

    except Exception as e:
        # Pass along the error message
        return f"Error scraping website {url}: {e}"


def get_scrape_tool():
    """
    Initializes and returns the wrapped Hyperbrowser scraping tool.
    """
    # This now returns our custom @tool-decorated function
    return scrape_website_with_hyperbrowser
