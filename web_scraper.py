import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from langchain_ollama import OllamaLLM
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import List, Dict
from typing import Optional
from pydantic import BaseModel
import sqlite3
import os

llm = OllamaLLM(model="llama3.2:1b")

class MovingCompany(BaseModel):
    name: Optional[str]
    locations_served: Optional[List[str]]  
    headquarters: Optional[str]            
    phone: Optional[str]                   
    website: Optional[str]                 
    rating: Optional[float]                
    services: Optional[List[str]]          
    years_in_business: Optional[int]       
    description: Optional[str]

class CompanyList(BaseModel):
    companies: Optional[List[MovingCompany]]


parser = PydanticOutputParser(pydantic_object=CompanyList)

prompt_template = PromptTemplate(
    template = """
You are an AI assistant for business data extraction.

Extract a list of **moving companies in the United States** from the given text. For each company, return:
- name
- locations_served (as a list of cities or states)
- headquarters (city + state)
- phone (US format or international)
- website (if available)
- rating (as a float, 0.0 to 5.0)
- services (as a list: e.g., "Residential", "Commercial", "Packing", "Storage")
- years_in_business (as an integer, if available)
- description (1-line summary)

The output should be formatted as JSON like this:

{{
  "companies": [
    {{
      "name": "Best Movers USA",
      "locations_served": ["New York", "New Jersey", "Connecticut"],
      "headquarters": "New York, NY",
      "phone": "+1-800-555-1234",
      "website": "https://www.bestmoversusa.com",
      "rating": 4.7,
      "services": ["Residential", "Commercial", "Packing"],
      "years_in_business": 12,
      "description": "Top-rated full-service moving company based in NYC."
    }},
    {{
      "name": "Swift Relocation",
      "locations_served": ["California", "Nevada"],
      "headquarters": "Los Angeles, CA",
      "phone": "+1-888-456-7890",
      "website": "https://www.swiftrelocation.com",
      "rating": 4.5,
      "services": ["Residential", "Storage"],
      "years_in_business": 8,
      "description": "Affordable movers with fast, reliable service."
    }}
  ]
}}

TEXT:
{text}
"""
,
    input_variables=["text"],
)


def get_search_results(query="best moving companies in US 2025", max_results=10):
    search_url = "https://html.duckduckgo.com/html/"
    params = {"q":query}
    headers = {"user-agent":"Mozilla/5.0"} #mimics a browser to avoid being blocked
    response = requests.post(search_url, data=params, headers=headers) 
    #response.text = full HTML page of search results
    #bs truns it into a searchable DOM tree
    soup = BeautifulSoup(response.text, "html.parser") 

    results = []
    #finds a <a> tags (links)
    for a in soup.select(".result__a")[:max_results]:
        #extract the href (url) and save it
        href = a["href"]
        results.append(href)

    #list of real URLs from search results
    return results


def scrap_page(url):
    try:
        print(f"Scrapping {url}")
        headers = {"User-Agent":"Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        #find all p tags (paragraphs)
        # .text.strip() gets the visible text
        text = "\n".join([p.text.strip() for p in soup.find_all("p")])
        #return preview (first 500 chars)
        return text
    
    except Exception as e:
        print(f"Failed to scrape {url}: {e}")
        return None
    

def extract_info(content):
    prompt = prompt_template.format(text=content[:3000])
    output = llm.invoke(prompt)

    if not output or "null" in output.lower():
        return None
    try:
        result = parser.parse(output)
        return result
    except Exception as e:
        print("Failed to parse output ")
        return None

def save_to_sql(companies, db_path="data/companies.db"):
    if not companies or not companies.companies:
        print("No movies to save.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        locations_served TEXT,
        headquarters TEXT,
        phone TEXT,
        website TEXT,
        rating REAL,
        services TEXT,
        years_in_business INTEGER,
        description TEXT
        );

    """)

    for company in companies.companies:
        if company:
            cursor.execute(
                """
                INSERT INTO companies (name, locations_served, headquarters, phone, website, rating, services, years_in_business, description)
                VALUES (?, ?, ?, ?, ?, ?, ? ,? ,?)
            """, (
                company.name,
                ",".join(company.locations_served or []),
                company.headquarters,
                company.phone,
                company.website,
                company.rating,
                ",".join(company.services or []),
                company.years_in_business,
                company.description

            ))
    conn.commit()
    conn.close()
    print(f"Saved {len(companies.companies)} movies to {db_path}")
    


urls = get_search_results()


for url in urls:
    content = scrap_page(url)
    if content:
        print("\n--- Preview of scraped content --- ")
        results = extract_info(content)
        if results:
            save_to_sql(results)
        else:
            print("Skipped saving due to parsing failure")
        print("\n==================================\n")