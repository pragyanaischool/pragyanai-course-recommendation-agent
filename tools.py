import os
from smolagents.tools import BaseTool  # ✅ Always available
from langchain_hyperbrowser import HyperbrowserScrapeTool


# --- API Key Setup ---
HYPERBROWSER_API_KEY = os.getenv("HYPERBROWSER_API_KEY")

_hyperbrowser_scraper = HyperbrowserScrapeTool(api_key=HYPERBROWSER_API_KEY)


def _scrape_website_with_hyperbrowser(url: str) -> str:
    """Internal function to scrape a website using Hyperbrowser."""
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


# --- ✅ FIX: Wrap it in a subclass of BaseTool ---
class HyperbrowserScrapeToolWrapper(BaseTool):
    name = "scrape_website_with_hyperbrowser"
    description = (
        "Scrapes a single website URL using Hyperbrowser and returns the content "
        "as Markdown text."
    )

    def forward(self, url: str) -> str:
        """Implements the tool execution logic."""
        return _scrape_website_with_hyperbrowser(url)


def get_scrape_tool():
    """Return a SmolAgents-compatible BaseTool instance."""
    return HyperbrowserScrapeToolWrapper()

