from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import json
import hashlib
import sys
from mongo_client import db # Import the MongoDB database instance

# --- Page Fetching Utility ---

def fetch_page(url, wait_for_selector=None, timeout=30000):
    """
    Fetches the HTML content of a page using Playwright.
    
    Args:
        url: The URL to scrape.
        wait_for_selector: A CSS selector to wait for before getting content.
        timeout: Max time to wait.
    
    Returns:
        The page's HTML content as a string, or None if it fails.
    """
    print(f"Fetching: {url}")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # Respect robots.txt (in a real scraper, you'd parse it)
            page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            
            if wait_for_selector:
                page.wait_for_selector(wait_for_selector, timeout=timeout)
            
            # Simple politeness delay
            time.sleep(2) 
            
            html = page.content()
            browser.close()
        return html
    except Exception as e:
        print(f"Error fetching page {url}: {e}")
        return None

# --- Site-Specific Adapters ---

def parse_course_generic(html: str, url: str) -> dict:
    """
    A generic parser using BeautifulSoup heuristics.
    This should be replaced with site-specific adapters.
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # Simple heuristics - replace with site-specific selectors
    title = soup.find(["h1", "h2"])
    desc = soup.find("meta", {"name": "description"}) or soup.find("p")
    price = None
    
    # Example: find price text heuristically
    price_text = soup.find(text=lambda t: t and ("₹" in t or "INR" in t or "$" in t))
    if price_text:
        price_str = "".join([c for c in price_text if c.isdigit()])
        price = int(price_str) if price_str else None

    return {
        "url": url,
        "title": title.get_text(strip=True) if title else "N/A",
        "description": desc.get("content") if desc and desc.get("content") else (desc.get_text(strip=True) if desc else "N/A"),
        "price": price,
        "raw_html": html  # Include raw HTML for the Analyzer Agent
    }

# --- Storage ---

def store_parsed(obj, outpath="courses_parsed.jsonl"):
    """
    Inserts a parsed course object into the 'raw_courses' MongoDB collection.
    Uses 'url' as a unique key to avoid duplicates.
    """
    if not db:
        print("Error: MongoDB not connected. Cannot store data.", file=sys.stderr)
        return

    try:
        # Use update_one with upsert=True to insert or update based on URL
        db.raw_courses.update_one(
            {'url': obj['url']},
            {'$set': obj},
            upsert=True
        )
    except Exception as e:
        print(f"Error inserting into MongoDB: {e}", file=sys.stderr)

# --- Main Execution ---

if __name__ == "__main__":
    """
    Main scraping script.
    """
    # Example list of URLs to scrape
    # Replace with real course URLs
    urls_to_scrape = [
        "https://example.com/course/data-science", 
        "https://example.org/course/web-development"
    ]
    
    if urls_to_scrape[0].startswith("https://example.com"):
        print("Please replace the placeholder URLs in `scraper.py` with real course URLs.")
        sys.exit(0)

    print(f"Starting scraper for {len(urls_to_scrape)} URLs...")

    for url in urls_to_scrape:
        # In a real app, you'd check robots.txt here
        # E.g., can_fetch = robot_parser.can_fetch("*", url)
        
        html = fetch_page(url, wait_for_selector="h1")
        
        if html:
            # Here you would select the correct adapter based on the URL
            # if "coursera.org" in url:
            #     parsed = parse_coursera(html, url)
            # else:
            parsed = parse_course_generic(html, url)
            
            parsed["scrape_ts"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            parsed["source_hash"] = hashlib.sha1(url.encode()).hexdigest()
            parsed["source"] = url.split('/')[2] # e.g., 'example.com'
            
            store_parsed(parsed) # This now saves to MongoDB
            print(f"Saved: {parsed['title']}")
        else:
            print(f"Failed to fetch: {url}")
            
    print("Scraping complete. Parsed data saved to MongoDB 'raw_courses' collection.")

