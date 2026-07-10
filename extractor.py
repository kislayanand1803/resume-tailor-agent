import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from typing import cast

# Import the scraper function we built in the last step!
from scraper import scrape_job_description

# 1. Load the secret API key from your .env file
load_dotenv(override=True)

# --- ADD THESE LINES TO DEBUG ---
print("--- DEBUGGING ENV LOAD ---")
api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
print(f"Key found in env: {api_key[:10] if api_key else 'NONE'}")
# --------------------------------

# We pass your specific GOOGLE_GEMINI_API_KEY from the .env file
client = genai.Client(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))

# 2. Build the "Mold" (The Pydantic Model)
# We are defining exactly what data we want the AI to extract.
class JobRequirements(BaseModel):
    job_title: str
    company_name: str
    core_skills: list[str] = Field(description="A clean list of the required technical and soft skills.")
    years_of_experience: int = Field(description="Minimum years of experience required. Output 0 if not specified.")
    key_responsibilities: list[str] = Field(description="A summarized list of the top 3-5 main responsibilities.")

# 3. The Extraction Function
def extract_requirements(raw_text: str) -> JobRequirements:
    """Passes messy text to Gemini and forces it to return clean, structured data."""
    print("Gemini is reading and extracting requirements...")
    
    # Grab the model name from your .env file
    model_name = os.getenv("GEMINI_EXTRACTOR_MODEL", "gemini-3.1-flash-lite")
    
    # We combine the instructions and the raw text for Gemini
    prompt = f"You are an expert technical recruiter. Extract the exact job requirements from the provided raw website text. Ignore cookie policies, navigation links, and irrelevant noise.\n\nRaw Text:\n{raw_text}"
    
    # We use Gemini's GenerateContentConfig to pass our Pydantic model
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=JobRequirements,
        ),
    )
    
    # Return the clean, parsed object casted to our Pydantic model
    return cast(JobRequirements, response.parsed)

# --- Test Block ---
if __name__ == "__main__":
    # 1. Provide a live URL
    test_url = "https://bebee.com/in/jobs/elektryk-przemyslowy-agencja-pracy-koncepcja-salem--gowork-0lmVAyb63ZTcO6xa3tR8XJ"
    
    # 2. Get the messy text using our previous script
    messy_text = scrape_job_description(test_url)
    
    # 3. Clean it up with Gemini
    clean_data = extract_requirements(messy_text)
    
    # 4. Look how perfectly structured it is!
    print("\n--- Cleaned Data ---")
    print(f"Company: {clean_data.company_name}")
    print(f"Title: {clean_data.job_title}")
    print(f"Experience Needed: {clean_data.years_of_experience} years")
    print("\nCore Skills:")
    for skill in clean_data.core_skills:
        print(f"- {skill}")
