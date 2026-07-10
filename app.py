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
    return response.text or "Error: The AI failed to generate a resume."

def generate_cover_letter(master_resume_text: str, job_requirements: JobRequirements) -> str:
    """Writes a compelling cover letter based on the resume and job requirements."""
    prompt = f"""
    You are an expert career coach and copywriter. 
    Write a highly compelling, modern cover letter for the job described below, using my Master Resume as the source of truth for my background.
    
    Guidelines:
    - Keep it concise (3-4 paragraphs max).
    - Match the tone of a modern tech/corporate professional.
    - Explicitly mention the company name and job title.
    - Highlight 1-2 specific achievements from my resume that prove I can handle their 'Key Responsibilities'.
    - Do not invent any experience.
    - Output in clean text/Markdown format.

    --- JOB REQUIREMENTS ---
    Company: {job_requirements.company_name}
    Title: {job_requirements.job_title}
    Key Responsibilities: {', '.join(job_requirements.key_responsibilities)}

    --- MY MASTER RESUME ---
    {master_resume_text}
    """
    
    response = client.models.generate_content(model=model_name, contents=prompt)
    return response.text or "Error: The AI failed to generate a cover letter."

# 1. Page Setup
st.set_page_config(page_title="AI Application Agent", page_icon="🎯", layout="centered")
st.title("🎯 Autonomous Application Agent")
st.write("Paste a job posting URL and your master resume to generate a hyper-targeted resume and cover letter.")

# 2. User Inputs
job_url = st.text_input("🔗 Job Posting URL", placeholder="https://boards.greenhouse.io/...")
master_resume = st.text_area("📄 Paste your Master Resume here", height=250, placeholder="Experience, Education, Projects...")

# 3. The "Run" Button
if st.button("Generate Application Package", type="primary"):
    
    if not job_url or not master_resume:
        st.warning("⚠️ Please provide both a job URL and your master resume!")
    else:
        with st.spinner("Scraping job description..."):
            messy_text = scrape_job_description(job_url)
            
        with st.spinner("Extracting structured requirements with Gemini..."):
            clean_requirements: JobRequirements = extract_requirements(messy_text)
            
            st.success(f"Found job: **{clean_requirements.job_title}** at **{clean_requirements.company_name}**")
            with st.expander("🔍 View Extracted Requirements"):
                st.write(f"**Experience Needed:** {clean_requirements.years_of_experience} years")
                st.write("**Core Skills:**", ", ".join(clean_requirements.core_skills))
                
        with st.spinner("Drafting your custom Resume and Cover Letter..."):
            # Generate both documents using the exact same extracted data
            final_resume = generate_tailored_resume(master_resume, clean_requirements)
            cover_letter = generate_cover_letter(master_resume, clean_requirements)
            
        # 4. Display the Final Results in Tabs
        st.divider()
        st.subheader("✨ Your Application Package")
        
        # Streamlit tabs make it easy to view multiple documents
        tab_resume, tab_cover_letter = st.tabs(["📄 Tailored Resume", "✉️ Cover Letter"])
        
        # Resume Tab
        with tab_resume:
            st.markdown(final_resume)
            st.download_button(
                label="Download Resume (.md)",
                data=final_resume,
                file_name=f"Resume_{clean_requirements.company_name.replace(' ', '_')}.md",
                mime="text/markdown"
            )
            
        # Cover Letter Tab
        with tab_cover_letter:
            st.markdown(cover_letter)
            st.download_button(
                label="Download Cover Letter (.md)",
                data=cover_letter,
                file_name=f"Cover_Letter_{clean_requirements.company_name.replace(' ', '_')}.md",
                mime="text/markdown"
            )