import os
from smolagents.tools import BaseTool
from langchain_hyperbrowser import HyperbrowserScrapeTool

# --- Load API Key ---
HYPERBROWSER_API_KEY = os.getenv("HYPERBROWSER_API_KEY")

# --- Initialize Hyperbrowser scraper ---
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


# ✅ FIXED: SmolAgents-Compatible Wrapper
class HyperbrowserScrapeToolWrapper(BaseTool):
    name = "scrape_website_with_hyperbrowser"
    description = (
        "Scrapes a single website URL using Hyperbrowser and returns the content "
        "as Markdown text."
    )

    def forward(self, url: str) -> str:
        return _scrape_website_with_hyperbrowser(url)

    def __call__(self, *args, **kwargs):
        if args:
            return self.forward(*args)
        elif "url" in kwargs:
            return self.forward(kwargs["url"])
        else:
            return "Error: Missing URL argument."

    # ✅ New method required by CodeAgent template
    def to_code_prompt(self) -> str:
        """Return the string prompt representation for the agent system message."""
        return f"{self.name}(url: str) -> str  # {self.description}"


def get_scrape_tool():
    """Return a SmolAgents-compatible BaseTool instance."""
    return HyperbrowserScrapeToolWrapper()
