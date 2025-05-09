import os
from dotenv import load_dotenv
import json
import time
import requests
from bs4 import BeautifulSoup
from html2text import HTML2Text
import logging
from langchain.text_splitter import CharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.chains.summarize import load_summarize_chain
from langchain_community.utilities import SerpAPIWrapper
from langchain_huggingface import HuggingFaceEndpoint
#from langchain_community.llms import HuggingFaceHub

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("moving_companies_scraper")

# Load environment variables
load_dotenv()
serper_api_key = os.getenv("SERPER_API_KEY")

# Initialize HuggingFace LLM (open source)
model_id = "tiiuae/falcon-7b-instruct"  # You can switch to other open source models
llm = HuggingFaceEndpoint(
    repo_id=model_id,
    huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
    temperature=0.1, 
    max_new_tokens= 500
)

# Smaller model for simpler tasks
small_llm = HuggingFaceEndpoint(
    repo_id="google/flan-t5-base",
    huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
    temperature=0.1,
    max_new_tokens=1000
)

def search_moving_companies(query="top moving companies in USA", num_results=10):
    """Search for moving companies using SerpAPI"""
    logger.info(f"Searching for: {query}")
    response = requests.get(
        "https://serpapi.com/search.json",
        params={
            "q": query,
            "location": "United States",
            "num": num_results,
            "serpapi_api_key": serper_api_key,
        }
    )
    response.raise_for_status()
    data = response.json()
    return data.get("organic_results", [])



def extract_company_urls(search_results):
    """Extract company URLs from search results"""
    company_urls = []
    for result in search_results:
        company_info = {
            "title": result.get("title"),
            "link": result.get("link"),
            "snippet": result.get("snippet")
        }
        company_urls.append(company_info)
    return company_urls

def extract_company_info(url_info):
    """Extract company information from their website"""
    title = url_info["title"]
    url = url_info["link"]
    snippet = url_info["snippet"]
    
    logger.info(f"Extracting info for: {title} from {url}")
    
    try:
        # Try to get the website content
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            logger.warning(f"Failed to retrieve content from {url}. Status code: {response.status_code}")
            return {
                "name": title,
                "website": url,
                "description": snippet,
                "phone": "N/A",
                "services": [],
                "source": "search",
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        
        # Parse website content
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Convert HTML to text
        h = HTML2Text()
        h.ignore_links = True
        h.ignore_images = True
        text_content = h.handle(response.text)
        
        # Extract phone number using pattern matching in BeautifulSoup
        phone = "N/A"
        # Look for common phone number patterns
        phone_patterns = [
            soup.find("a", href=lambda href: href and "tel:" in href),
            soup.find(text=lambda text: text and any(p in text for p in ["Call us", "Phone:", "Tel:"]))
        ]
        
        for pattern in phone_patterns:
            if pattern:
                # Extract phone number - simplified approach
                if hasattr(pattern, "href"):
                    phone = pattern.get("href").replace("tel:", "")
                else:
                    phone = pattern.find_parent().get_text().strip()
                break
        
        # Use LLM to extract services
        services_prompt = PromptTemplate(
            template="""
            From the following company description, extract the moving services they offer.
            Return only a comma-separated list of services. If you can't determine the services, return "General Moving Services".
            
            Description: {description}
            
            Services:
            """,
            input_variables=["description"]
        )
        
        services_chain = LLMChain(llm=small_llm, prompt=services_prompt)
        services_text = services_chain.run(description=text_content[:5000])  # Limit text to avoid token limits
        services = [service.strip() for service in services_text.split(",")]
        
        # Use LLM to generate a concise description
        if len(text_content) > 1000:
            description_prompt = PromptTemplate(
                template="""
                Summarize the following moving company description in 2-3 sentences:
                
                {text}
                
                Concise summary:
                """,
                input_variables=["text"]
            )
            
            # Split text into manageable chunks
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
            docs = text_splitter.create_documents([text_content[:10000]])  # Limit to first 10k chars
            
            # Create and run the chain
            chain = load_summarize_chain(
                llm=llm,
                chain_type="map_reduce",
                map_prompt=description_prompt,
                combine_prompt=description_prompt,
                verbose=False
            )
            
            description = chain.run(input_documents=docs)
        else:
            description = snippet
        
        return {
            "name": title,
            "website": url,
            "description": description,
            "phone": phone,
            "services": services,
            "source": "website",
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    except Exception as e:
        logger.error(f"Error extracting info from {url}: {str(e)}")
        return {
            "name": title,
            "website": url,
            "description": snippet,
            "phone": "N/A",
            "services": [],
            "source": "search",
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "error": str(e)
        }

def enrich_with_additional_data(company_info):
    """Enrich company data with additional information from SerpAPI"""
    company_name = company_info["name"]
    
    try:
        logger.info(f"Enriching data for: {company_name}")
        # Search for company contact info
        search = SerpAPIWrapper(
            serper_api_key=serper_api_key,
            k=3
        )
        results = search.results(f"{company_name} moving company contact information")
        
        # Generate address and additional contact info using LLM
        contact_prompt = PromptTemplate(
            template="""
            Given the following search results about a moving company, extract:
            1. The company's address (if available)
            2. Any additional phone numbers (if available)
            3. Email address (if available)
            
            Format your response as JSON with these fields: "address", "additional_phones", "email"
            
            Search results:
            {results}
            
            JSON Response:
            """,
            input_variables=["results"]
        )
        
        contact_chain = LLMChain(llm=small_llm, prompt=contact_prompt)
        contact_info_text = contact_chain.run(results=json.dumps(results["organic"][:3]))
        
        # Parse the JSON response
        try:
            additional_info = json.loads(contact_info_text)
            company_info.update(additional_info)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse contact info for {company_name}")
            # Add empty fields if parsing fails
            company_info.update({
                "address": "N/A",
                "additional_phones": [],
                "email": "N/A"
            })
        
        return company_info
        
    except Exception as e:
        logger.error(f"Error enriching data for {company_name}: {str(e)}")
        company_info.update({
            "address": "N/A",
            "additional_phones": [],
            "email": "N/A"
        })
        return company_info

def main():
    """Main function to run the scraper"""
    data_dir = "./data"
    os.makedirs(data_dir, exist_ok=True)
    
    # Search for nationwide moving companies
    nationwide_results = search_moving_companies("top nationwide moving companies USA", 5)
    
    # Search for regional moving companies across different regions
    regions = ["East Coast", "West Coast", "Midwest", "South"]
    regional_results = []
    
    for region in regions:
        regional_query = f"best moving companies {region} USA"
        regional_results.extend(search_moving_companies(regional_query, 3))
    
    # Combine results
    all_results = nationwide_results + regional_results
    company_urls = extract_company_urls(all_results)
    
    # Extract company information
    logger.info("Extracting company information...")
    companies = []
    
    for url_info in company_urls:
        company_info = extract_company_info(url_info)
        
        # Skip duplicate companies
        if any(comp["name"] == company_info["name"] for comp in companies):
            continue
            
        # Enrich with additional data
        enriched_info = enrich_with_additional_data(company_info)
        companies.append(enriched_info)
        
        # Sleep to avoid rate limiting
        time.sleep(2)
    
    # Save to JSON file
    output_file = os.path.join(data_dir, "moving_companies.json")
    with open(output_file, 'w') as f:
        json.dump(companies, f, indent=2)
    
    logger.info(f"Saved {len(companies)} companies to {output_file}")
    return companies

if __name__ == "__main__":
    main()