import os
import json
import requests
import time
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from openai import OpenAI
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# Load API Key
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# Set up OpenAI client
openai = OpenAI(api_key=api_key)
MODEL = "gpt-4o-mini"

# Configure Selenium for JavaScript-heavy websites
def get_dynamic_page_source(url):
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    #options.binary_location = "/usr/bin/google-chrome"

    service = Service(ChromeDriverManager().install())  # Install driver automatically
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        time.sleep(3)  # Wait for JavaScript to load
        page_source = driver.page_source
    finally:
        driver.quit()

    return page_source

class Website:
    def __init__(self, url):
        self.url = url
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
            response.raise_for_status()
            self.body = response.content
        except requests.exceptions.RequestException:
            # Fallback to Selenium if requests fails
            self.body = get_dynamic_page_source(url)

        soup = BeautifulSoup(self.body, 'html.parser')
        self.title = soup.title.string if soup.title else "No title found"
        
        if soup.body:
            for irrelevant in soup.body(["script", "style", "img", "input"]):
                irrelevant.decompose()
            self.text = soup.body.get_text(separator="\n", strip=True)
        else:
            self.text = ""

        self.links = [link.get('href') for link in soup.find_all('a') if link.get('href')]

    def get_contents(self):
        return f"Webpage Title:\n{self.title}\nWebpage Contents:\n{self.text}\n\n"

def get_links(url):
    website = Website(url)
    
    system_prompt = (
        "You are an assistant that extracts relevant company website links "
        "for a brochure. Respond strictly in JSON format."
    )

    user_prompt = (
        f"Here is the list of links found on {website.url}. Identify the most relevant links for a company brochure.\n\n"
        "Only include links that are important for company presentation, such as:\n"
        "- About Us\n"
        "- Careers\n"
        "- Contact\n"
        "- Services/Products\n\n"
        "Respond **only** in JSON format like this:\n"
        "{\n"
        '    "links": [\n'
        '        {"type": "about page", "url": "https://example.com/about"},\n'
        '        {"type": "careers page", "url": "https://example.com/careers"}\n'
        "    ]\n"
        "}"
    )

    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"}  # Corrected format
    )

    result = response.choices[0].message.content
    return json.loads(result)



def generate_brochure(company_name, url, language="English"):
    content = Website(url).get_contents()
    links = get_links(url)

    details = f"Landing Page:\n{content}\n"
    for link in links.get("links", []):
        details += f"\n\n{link['type']}\n{Website(link['url']).get_contents()}"

    language_prompt = {
        "English": "Generate a professional and engaging brochure in English for a company, formatted in markdown. Include headings for sections like 'Company Overview', 'Products', 'Contact Information', and 'Services'. Ensure proper use of bullet points, headings, and clear spacing for readability.",
        "Spanish": "Genera un folleto profesional y atractivo en español para una empresa, formateado en markdown. Incluye encabezados para secciones como 'Visión General de la Empresa', 'Productos', 'Información de Contacto' y 'Servicios'. Asegúrate de usar correctamente los puntos de lista, los encabezados y un espaciado claro para facilitar la lectura."

    }

    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": language_prompt[language]},
            {"role": "user", "content": details[:5_000]}
        ]
    )
    return response.choices[0].message.content
