import json
from llm_client import call_llm
from data_models import Course
import time
from mongo_client import db # Import the MongoDB database instance
from pymongo.errors import BulkWriteError

# --- Prompts ---

ANALYZER_SYSTEM_PROMPT = """
You are a Course Analyzer Agent. Your task is to extract structured information from raw course data.
You must output *only* a valid JSON object matching the `Course` schema provided.
Do not add any text before or after the JSON.
- `skills_taught`: List of specific, marketable skills.
- `prerequisites`: List of required skills or knowledge.
- `level`: Must be one of 'Beginner', 'Intermediate', 'Advanced'.
- `placement_type`: Must be one of 'guarantee', 'assistance', 'none'.
- `placement_stats`: Extract `historical_rate` (as a float 0.0-1.0) and `median_salary` (as an int).
- `trust_score`: A float 0.0-1.0. Base this on signals: provider reputation (if known), number of reviews, clarity of placement policy, and whether salary claims seem realistic. Penalize for vague or unverifiable claims.
- `placement_claim_text`: The literal text of any placement claim.
- If a provider makes a "guarantee", set `trust_score` lower (e.g., 0.5) unless strong evidence is present, and note that it requires verification.
"""

def get_course_schema_prompt():
    """Returns a string representation of the Course schema for the prompt."""
    # Using model_json_schema() for an accurate representation
    return json.dumps(Course.model_json_schema(), indent=2)

def get_analyzer_user_prompt(raw_data: dict) -> str:
    """
    Formats the raw scraped data into a user prompt for the LLM.
    We only include the fields the LLM needs to analyze.
    """
    
    # Truncate description/HTML to fit context window
    description = raw_data.get('description', '')[:1000]
    raw_html_snippet = raw_data.get('raw_html', '')[:2000] # Analyze a snippet
    
    prompt_data = {
        "title": raw_data.get('title'),
        "description_snippet": description,
        "url": raw_data.get('url'),
        "provider_name": raw_data.get('source'), # Use source as provider
        "price": raw_data.get('price'),
        "raw_html_snippet": raw_html_snippet # Give it a snippet to find claims
    }
    return json.dumps(prompt_data, indent=2)

# --- Main Execution ---

def analyze_courses(inpath="courses_parsed.jsonl", outpath="courses_structured.jsonl"):
    """
    Reads raw parsed courses from MongoDB 'raw_courses' collection,
    runs them through the Analyzer Agent (LLM),
    and saves the structured, validated data to 'structured_courses' collection.
    """
    if not db:
        print("Error: MongoDB not connected. Cannot run analysis.")
        return

    print("Starting Course Analysis Pipeline...")
    structured_courses_to_write = []
    
    try:
        # Find raw courses that haven't been structured yet
        # A more robust way would be to check a timestamp or 'processed' flag
        # For simplicity, we find all raw courses.
        raw_courses = list(db.raw_courses.find())
    except Exception as e:
        print(f"Error reading from 'raw_courses' collection: {e}")
        return
    
    if not raw_courses:
        print("No raw courses found in MongoDB. Please run `scraper.py` first.")
        return

    full_system_prompt = f"{ANALYZER_SYSTEM_PROMPT}\n\nHere is the target JSON schema:\n{get_course_schema_prompt()}"

    for i, raw_data in enumerate(raw_courses):
        print(f"Analyzing course {i+1}/{len(raw_courses)}: {raw_data.get('title', 'N/A')}")
        
        user_prompt = get_analyzer_user_prompt(raw_data)
        
        # Call the LLM with JSON mode
        llm_output = call_llm(full_system_prompt, user_prompt, use_json=True)
        
        if llm_output and not llm_output.get('error'):
            try:
                # Merge original data with LLM-extracted data
                # LLM output *is* the new structured data
                
                # Add back essential fields from raw data
                llm_output['course_id'] = f"{raw_data.get('source', 'unknown')}::{raw_data.get('source_hash', 'nohash')}"
                llm_output['source'] = raw_data.get('source')
                llm_output['url'] = raw_data.get('url')
                llm_output['title'] = raw_data.get('title')
                llm_output['description'] = raw_data.get('description')
                llm_output['price'] = raw_data.get('price', 0)
                llm_output['last_scraped'] = raw_data.get('scrape_ts')
                
                # Set defaults for fields LLM might miss
                if 'currency' not in llm_output:
                    llm_output['currency'] = 'INR'
                if 'mode' not in llm_output or not llm_output['mode']:
                    llm_output['mode'] = ['online_live'] # Default

                # Validate with Pydantic
                course = Course.model_validate(llm_output)
                structured_courses_to_write.append(course.model_dump())
                
            except Exception as e:
                print(f"Validation Error for course {raw_data.get('title')}: {e}")
                print(f"LLM Output was: {llm_output}")
        else:
            print(f"Failed to analyze course {raw_data.get('title')}: {llm_output.get('error', 'Unknown LLM error')}")
        
        # Rate limit API calls
        time.sleep(1) 

    # Write structured data to new MongoDB collection
    if structured_courses_to_write:
        print(f"Writing {len(structured_courses_to_write)} structured courses to MongoDB...")
        try:
            for course_data in structured_courses_to_write:
                # Use update_one with upsert=True to insert or update based on course_id
                db.structured_courses.update_one(
                    {'course_id': course_data['course_id']},
                    {'$set': course_data},
                    upsert=True
                )
            print(f"Analysis complete. Saved {len(structured_courses_to_write)} structured courses to 'structured_courses' collection.")
        except BulkWriteError as bwe:
            print(f"MongoDB Bulk Write Error: {bwe.details}")
        except Exception as e:
            print(f"Error writing to 'structured_courses' collection: {e}")
    else:
        print("No new courses were successfully analyzed.")


if __name__ == "__main__":
    analyze_courses()

