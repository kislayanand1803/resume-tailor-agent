import os
from dotenv import load_dotenv
from google import genai

# We are importing the hard work we already did, PLUS the JobRequirements model!
from scraper import scrape_job_description
from extractor import extract_requirements, JobRequirements

# Load environment
load_dotenv(override=True)
client = genai.Client(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))
model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Added type hints so VS Code knows exactly what 'job_requirements' is
def generate_tailored_resume(master_resume_text: str, job_requirements: JobRequirements) -> str:
    """Takes your master resume and the job requirements, and rewrites it."""
    
    prompt = f"""
    You are an expert executive resume writer. 
    I am going to give you my Master Resume and the specific requirements for a job I want.
    
    Please rewrite my resume to highlight the skills and experiences that best match the job requirements. 
    - Do not lie or invent experience. If I do not have a required skill, leave it out.
    - Tailor the professional summary and bullet points to match the keywords from the job.
    - Output the final resume in clean Markdown format.

    --- JOB REQUIREMENTS ---
    Company: {job_requirements.company_name}
    Title: {job_requirements.job_title}
    Core Skills: {', '.join(job_requirements.core_skills)}
    Key Responsibilities: {', '.join(job_requirements.key_responsibilities)}

    --- MY MASTER RESUME ---
    {master_resume_text}
    """

    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )
    
    return response.text or "Error: The AI failed to generate a response."

# --- Run the Full Agent ---
if __name__ == "__main__":
    # 1. Provide your live job URL
    job_url = "https://bebee.com/in/jobs/elektryk-przemyslowy-agencja-pracy-koncepcja-salem--gowork-0lmVAyb63ZTcO6xa3tR8XJ"
    
    # 2. Get the Job Requirements (Agent Step 1 & 2)
    print("Step 1: Scraping and extracting job requirements...")
    messy_text = scrape_job_description(job_url)
    
    # Explicitly declare the type here as well to satisfy Pylance
    clean_requirements: JobRequirements = extract_requirements(messy_text)
    
    print(f"-> Found job: {clean_requirements.job_title} at {clean_requirements.company_name}")
    
    # 3. Read your Master Resume
    try:
        with open("master_resume.txt", "r", encoding="utf-8") as file:
            master_resume = file.read()
    except FileNotFoundError:
        print("Error: Please create a 'master_resume.txt' file and paste your resume text inside.")
        exit()
        
    # 4. Generate the new tailored resume (Agent Step 3)
    print("\nStep 2: Tailoring your resume...")
    final_resume = generate_tailored_resume(master_resume, clean_requirements)
    
    # 5. Save it to a brand new Markdown file
    output_filename = f"Tailored_Resume_{clean_requirements.company_name.replace(' ', '_')}.md"
    
    with open(output_filename, "w", encoding="utf-8") as file:
        file.write(final_resume)
        
    print(f"\nSUCCESS! Your tailored resume has been saved as: {output_filename}")