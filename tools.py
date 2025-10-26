import os
from smolagents.tools import PythonTool  # ✅ correct BaseTool subclass
from langchain_hyperbrowser import HyperbrowserScrapeTool

# Load the Hyperbrowser API key
HYPERBROWSER_API_KEY = os.getenv("HYPERBROWSER_API_KEY")

# Initialize the Hyperbrowser scraper
_hyperbrowser_scraper = HyperbrowserScrapeTool(api_key=HYPERBROWSER_API_KEY)

def _scrape_website_with_hyperbrowser(url: str) -> str:
    """Scrape a website using Hyperbrowser."""
    if not HYPERBROWSER_API_KEY:
        return "Error: HYPERBROWSER_API_KEY environment variable is not set."

    try:
        result = _hyperbrowser_scraper.invoke(
            {"url": url, "scrape_options": {"formats": ["markdown"]}}
        )
        if isinstance(result, dict) and result.get("markdown"):
            return result["markdown"]
        return str(result)
    except Exception as e:
        return f"Error scraping website {url}: {e}"

def get_scrape_tool():
    """Return a SmolAgents-compatible scraping tool."""
    scrape_tool = PythonTool(
        name="scrape_website_with_hyperbrowser",
        description=(
            "Scrapes a single website URL using Hyperbrowser and returns Markdown text content."
        ),
        func=_scrape_website_with_hyperbrowser,  # ✅ Must be a Python callable
    )
    return scrape_tool


