from docx import Document
import io
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

# --- CORE FUNCTIONS ---
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

def generate_cover_letter(master_resume_text: str, job_requirements: JobRequirements) -> str:
    """Writes a highly targeted cover letter using a strict professional template."""
    prompt = f"""
    You are an expert career coach. Write a persuasive, professional cover letter 
    for the following job, using my Master Resume as the foundation.
    
    You MUST adhere strictly to the following structural template, keeping the letter to one page:
    
    1. Header: [My Name | Address | Phone | Email]
    2. Recipient: [Company Name | Address | Contact Person if known]
    3. Regarding: [Specific Job Title] - [Current Date]
    4. Headline: A catchy, 1-sentence headline containing relevant experience or unique selling points.
    5. Motivation (5-7 lines): Be detailed and honest about why I am excited about the specific tasks and the company.
    6. Professional Qualifications: Present my relevant study programs, knowledge (subjects/projects), and link them directly to the specific tasks in the job ad. Use specific examples.
    7. Personality: Present key personal competencies relevant to what the company asks for, showing brief examples (e.g., "team player from 3 years of competitive sports").
    8. Closing (3-4 lines): Confidently pave the way for an interview. Do NOT use passive phrases like "I hope to hear from you."
    9. Sign-off: "Kind regards,\n[My Name]"

    --- JOB REQUIREMENTS ---
    Company: {job_requirements.company_name}
    Title: {job_requirements.job_title}
    Core Skills: {', '.join(job_requirements.core_skills)}
    Key Responsibilities: {', '.join(job_requirements.key_responsibilities)}

    --- MY MASTER RESUME ---
    {master_resume_text}
    """
    
    response = client.models.generate_content(model=model_name, contents=prompt)
    return response.text or "Error: The AI failed to generate a cover letter."

def create_docx(text: str) -> io.BytesIO:
    """Converts raw text into a downloadable Word Document."""
    doc = Document()
    
    # Split the text by lines and add them as paragraphs
    for line in text.split('\n'):
        doc.add_paragraph(line)
        
    # Save the document to a virtual memory file (BytesIO) instead of the hard drive
    bio = io.BytesIO()
    doc.save(bio)
    return bio
    
# --- STREAMLIT USER INTERFACE ---

# 1. Page Setup
st.set_page_config(page_title="AI Resume Tailor", page_icon="🎯", layout="centered")
st.title("🎯 Autonomous Resume Tailor")
st.write("Generate a hyper-targeted resume and cover letter in seconds.")

# 2. Master Resume Input
master_resume = st.text_area("📄 Paste your Master Resume here", height=200, placeholder="Experience, Education, Projects...")

st.divider()

# 3. Input Method Toggle (V2.1 Feature)
st.subheader("🔗 Job Details")
input_method = st.radio(
    "How do you want to provide the job description?",
    ["Paste a URL", "Paste the Text Manually (Best for LinkedIn/Indeed)"]
)

# Show the correct input box based on the user's choice
job_url = ""
job_text = ""

if input_method == "Paste a URL":
    job_url = st.text_input("Job Posting URL", placeholder="https://boards.greenhouse.io/...")
else:
    job_text = st.text_area("Raw Job Description", height=200, placeholder="Copy and paste the full job description text here...")

# 4. The "Run" Button
if st.button("Tailor My Application", type="primary"):
    
    # Safety check: ensure resume exists
    if not master_resume:
        st.warning("⚠️ Please provide your master resume!")
        st.stop()
        
    messy_text = ""
    
    # Handle the URL Scraping Route
    if input_method == "Paste a URL":
        if not job_url:
            st.warning("⚠️ Please provide a job URL!")
            st.stop()
            
        with st.spinner("Scraping job description from web..."):
            messy_text = scrape_job_description(job_url)
            
    # Handle the Manual Text Route
    else:
        if not job_text:
            st.warning("⚠️ Please paste the job description text!")
            st.stop()
        messy_text = job_text

    # Extract Requirements
    with st.spinner("Extracting structured requirements with Gemini..."):
        clean_requirements: JobRequirements = extract_requirements(messy_text)
        
        # --- V2.1 ANTI-BOT DETECTOR ---
        # If Gemini outputs "Not found", we know the scraper got blocked by a Captcha or 403 error.
        if clean_requirements.company_name.lower() in ["not found", "unknown"] or clean_requirements.job_title.lower() in ["not found", "unknown"]:
            st.error("🚨 **Web Scraper Blocked!**")
            st.write("The website's anti-bot security (like LinkedIn or Indeed) blocked our script from reading the page.")
            st.info("💡 **Quick Fix:** Switch the toggle above to **'Paste the Text Manually'**, copy the text directly from the job site, and paste it into the box!")
            st.stop() # Stops the rest of the code from running
            
        # Show the user what we extracted successfully
        st.success(f"Found job: **{clean_requirements.job_title}** at **{clean_requirements.company_name}**")
        with st.expander("🔍 View Extracted Requirements"):
            st.write(f"**Experience Needed:** {clean_requirements.years_of_experience} years")
            st.write("**Core Skills:**", ", ".join(clean_requirements.core_skills))
            
    # Generate Documents
    with st.spinner("Rewriting your resume and crafting a cover letter..."):
        final_resume = generate_tailored_resume(master_resume, clean_requirements)
        final_cover_letter = generate_cover_letter(master_resume, clean_requirements)
        
    # 5. Display the Final Results using Tabs
    st.divider()
    st.subheader("✨ Your Tailored Application")
    
    tab1, tab2 = st.tabs(["📄 Tailored Resume", "✉️ Cover Letter"])
    
    with tab1:
        st.markdown(final_resume)
        st.download_button(
            label="Download Resume (.md)",
            data=final_resume,
            file_name=f"Resume_{clean_requirements.company_name.replace(' ', '_')}.md",
            mime="text/markdown"
        )
        
    with tab2:
        st.markdown(final_cover_letter)
        
        # Convert the markdown text to a Word Document
        docx_file = create_docx(final_cover_letter)
        
        # Docx Download Button
        st.download_button(
            label="📥 Download Cover Letter (.docx)",
            data=docx_file.getvalue(),
            file_name=f"Cover_Letter_{clean_requirements.company_name.replace(' ', '_')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
