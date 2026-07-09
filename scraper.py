import requests
from bs4 import BeautifulSoup

def scrape_job_description(url):
    """Fetches a URL and returns the visible text from the page."""
    
    # We use a headers dictionary to pretend to be a standard web browser. 
    # Without this, many job boards will block the request thinking it's a malicious bot.
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        print(f"Fetching URL: {url}...")
        response = requests.get(url, headers=headers)
        
        # This will immediately stop the script if the website returns a 404 Not Found or 403 Forbidden
        response.raise_for_status() 
        
        # Parse the raw HTML into a readable format
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract only the text, replacing HTML tags with newlines
        raw_text = soup.get_text(separator='\n', strip=True)
        
        return raw_text
        
    except Exception as e:
        return f"Error scraping the page: {e}"

# --- Test Block ---
# This code only runs if you execute this file directly.
if __name__ == "__main__":
    # Let's test it on a public Greenhouse job posting
    test_job_url = "https://bebee.com/in/jobs/elektryk-przemyslowy-agencja-pracy-koncepcja-salem--gowork-0lmVAyb63ZTcO6xa3tR8XJ" 
    
    job_text = scrape_job_description(test_job_url)
    
    print("\n--- Extracted Text Preview ---\n")
    # We only print the first 1000 characters so it doesn't flood your terminal
    print(job_text[:1000])