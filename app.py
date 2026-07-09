import os
import streamlit as st
from dotenv import load_dotenv
from google import genai

# Import the tools you already built!
from scraper import scrape_job_description
from extractor import extract_requirements, JobRequirements

# Load environment
load_dotenv(override=True)
client = genai.Client(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))
model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# --- CORE FUNCTION ---
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
    
    response = client.models.generate_content(model=model_name, contents=prompt)
    return response.text or "Error: The AI failed to generate a response."

# --- STREAMLIT USER INTERFACE ---

# 1. Page Setup
st.set_page_config(page_title="AI Resume Tailor", page_icon="🎯", layout="centered")
st.title("🎯 Autonomous Resume Tailor")
st.write("Paste a job posting URL and your master resume to generate a hyper-targeted application.")

# 2. User Inputs
job_url = st.text_input("🔗 Job Posting URL", placeholder="https://boards.greenhouse.io/...")
master_resume = st.text_area("📄 Paste your Master Resume here", height=250, placeholder="Experience, Education, Projects...")

# 3. The "Run" Button
if st.button("Tailor My Resume", type="primary"):
    
    # Safety check: make sure the user actually entered data
    if not job_url or not master_resume:
        st.warning("⚠️ Please provide both a job URL and your master resume!")
    else:
        # We use st.spinner to show a loading animation while the agent works
        with st.spinner("Scraping job description..."):
            messy_text = scrape_job_description(job_url)
            
        with st.spinner("Extracting structured requirements with Gemini..."):
            clean_requirements: JobRequirements = extract_requirements(messy_text)
            
            # Show the user what we extracted
            st.success(f"Found job: **{clean_requirements.job_title}** at **{clean_requirements.company_name}**")
            with st.expander("🔍 View Extracted Requirements"):
                st.write(f"**Experience Needed:** {clean_requirements.years_of_experience} years")
                st.write("**Core Skills:**", ", ".join(clean_requirements.core_skills))
                
        with st.spinner("Rewriting your resume to match..."):
            final_resume = generate_tailored_resume(master_resume, clean_requirements)
            
        # 4. Display the Final Result
        st.divider()
        st.subheader("✨ Your Tailored Resume")
        
        # Display it nicely on the screen
        st.markdown(final_resume)
        
        # 5. Add a Download Button!
        st.download_button(
            label="Download as Markdown (.md)",
            data=final_resume,
            file_name=f"Tailored_Resume_{clean_requirements.company_name.replace(' ', '_')}.md",
            mime="text/markdown"
        )