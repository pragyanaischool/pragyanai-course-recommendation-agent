from langchain_community.tools.web_scraping import ScrapeWebsiteTool

def get_scrape_tool():
    """
    Initializes and returns the website scraping tool.
    """
    # This tool is simple and effective for extracting text.
    return ScrapeWebsiteTool()
