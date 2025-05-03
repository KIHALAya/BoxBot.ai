import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import os
import time
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("web_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("web_scraper")

class MovingCompanyScraper:
    def __init__(self, data_path="./data"):
        """Initialize the scraper with a path to save data"""
        self.data_path = data_path
        self.companies_file = os.path.join(data_path, "moving_companies.json")
        
        # Create data directory if it doesn't exist
        if not os.path.exists(data_path):
            os.makedirs(data_path)
            
        # Load existing companies if file exists
        self.companies = self._load_existing_companies()
        
    def _load_existing_companies(self):
        """Load existing companies from file if it exists"""
        if os.path.exists(self.companies_file):
            try:
                with open(self.companies_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Error loading companies file: {self.companies_file}")
                return []
        return []
    
    def save_companies(self):
        """Save companies to JSON file"""
        with open(self.companies_file, 'w') as f:
            json.dump(self.companies, f, indent=2)
        logger.info(f"Saved {len(self.companies)} companies to {self.companies_file}")
    
    def scrape_mymovingreviews(self):
        """Scrape moving companies from mymovingreviews.com"""
        url = "https://www.mymovingreviews.com/find/top-rated-moving-companies"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Failed to retrieve MyMovingReviews. Status code: {response.status_code}")
                return []
                
            soup = BeautifulSoup(response.text, 'html.parser')
            company_listings = soup.select('.company-listing')
            
            companies = []
            for listing in company_listings[:20]:  # Limit to top 20
                try:
                    name_elem = listing.select_one('.company-name')
                    if name_elem:
                        name = name_elem.text.strip()
                        
                        # Extract phone if available
                        phone_elem = listing.select_one('.phone-number')
                        phone = phone_elem.text.strip() if phone_elem else "N/A"
                        
                        # Extract website if available
                        website_elem = listing.select_one('.website a')
                        website = website_elem['href'] if website_elem else "N/A"
                        
                        companies.append({
                            "name": name,
                            "phone": phone,
                            "website": website,
                            "source": "mymovingreviews.com",
                            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                except Exception as e:
                    logger.error(f"Error parsing company listing: {e}")
                    continue
                    
            return companies
        
        except Exception as e:
            logger.error(f"Error scraping MyMovingReviews: {e}")
            return []
    
    def scrape_movingcom(self):
        """Scrape moving companies from moving.com"""
        url = "https://www.moving.com/movers/moving-companies.asp"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Failed to retrieve Moving.com. Status code: {response.status_code}")
                return []
                
            soup = BeautifulSoup(response.text, 'html.parser')
            company_cards = soup.select('.moving-company-card')
            
            companies = []
            for card in company_cards[:20]:  # Limit to top 20
                try:
                    name_elem = card.select_one('.company-name')
                    if name_elem:
                        name = name_elem.text.strip()
                        
                        # Extract phone if available
                        phone_elem = card.select_one('.phone')
                        phone = phone_elem.text.strip() if phone_elem else "N/A"
                        
                        # Extract website if available (simplified)
                        website = "N/A"
                        
                        companies.append({
                            "name": name,
                            "phone": phone,
                            "website": website,
                            "source": "moving.com",
                            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                except Exception as e:
                    logger.error(f"Error parsing company card: {e}")
                    continue
                    
            return companies
        
        except Exception as e:
            logger.error(f"Error scraping Moving.com: {e}")
            return []
    
    def scrape_angies_list(self):
        """Scrape moving companies from Angie's List (simplified)"""
        # This is a mock implementation since Angie's List requires authentication
        # In a real implementation, you'd need to handle login/authentication
        
        # Return mock data for demonstration
        mock_companies = [
            {
                "name": "Two Men and a Truck",
                "phone": "(800) 345-1070",
                "website": "https://www.twomenandatruck.com",
                "source": "angies_list",
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            {
                "name": "United Van Lines",
                "phone": "(800) 948-4885",
                "website": "https://www.unitedvanlines.com",
                "source": "angies_list",
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            {
                "name": "Atlas Van Lines",
                "phone": "(800) 638-9797",
                "website": "https://www.atlasvanlines.com",
                "source": "angies_list",
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        ]
        
        return mock_companies
    
    def update_companies(self):
        """Scrape all sources and update the company list"""
        logger.info("Starting company data update...")
        
        # Get companies from each source
        mymovingreviews_companies = self.scrape_mymovingreviews()
        movingcom_companies = self.scrape_movingcom()
        angies_list_companies = self.scrape_angies_list()
        
        # Combine all results
        all_new_companies = mymovingreviews_companies + movingcom_companies + angies_list_companies
        
        # Update existing companies or add new ones
        company_names = {company["name"] for company in self.companies}
        
        for company in all_new_companies:
            if company["name"] not in company_names:
                self.companies.append(company)
                company_names.add(company["name"])
            else:
                # Update existing company info
                for i, existing_company in enumerate(self.companies):
                    if existing_company["name"] == company["name"]:
                        self.companies[i] = company
                        break
        
        # Save updated company list
        self.save_companies()
        
        return self.companies
    
    def get_companies(self):
        """Return the current list of companies"""
        return self.companies

    def get_company_names(self):
        """Return just the names of companies for UI display"""
        return [company["name"] for company in self.companies]


def run_scraper_update():
    """Run the scraper update as a standalone process"""
    scraper = MovingCompanyScraper()
    companies = scraper.update_companies()
    logger.info(f"Updated {len(companies)} companies")
    return companies


if __name__ == "__main__":
    run_scraper_update()