import schedule
import time
import threading
import logging
from web_scraper import MovingCompanyScraper
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("scheduler")

class SchedulerManager:
    def __init__(self, data_path="./data"):
        """Initialize the scheduler manager"""
        self.scraper = MovingCompanyScraper(data_path=data_path)
        self.scheduler_thread = None
        self.is_running = False
        
    def update_companies_job(self):
        """Job to update companies list"""
        logger.info(f"Running scheduled company update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        try:
            companies = self.scraper.update_companies()
            logger.info(f"Updated company list with {len(companies)} companies")
            return companies
        except Exception as e:
            logger.error(f"Error updating companies: {e}")
            return []
    
    def start_scheduler(self, update_interval='24h'):
        """Start the scheduler with the specified interval"""
        if self.is_running:
            logger.info("Scheduler already running")
            return
            
        self.is_running = True
        
        # Parse the update interval
        if update_interval.endswith('h'):
            hours = int(update_interval[:-1])
            schedule.every(hours).hours.do(self.update_companies_job)
            logger.info(f"Scheduler set to run every {hours} hours")
        elif update_interval.endswith('m'):
            minutes = int(update_interval[:-1])
            schedule.every(minutes).minutes.do(self.update_companies_job)
            logger.info(f"Scheduler set to run every {minutes} minutes")
        elif update_interval.endswith('d'):
            days = int(update_interval[:-1])
            schedule.every(days).days.do(self.update_companies_job)
            logger.info(f"Scheduler set to run every {days} days")
        else:
            # Default to daily
            schedule.every().day.do(self.update_companies_job)
            logger.info("Scheduler set to run daily")
        
        # Run the job once immediately
        self.update_companies_job()
        
        # Start the scheduler in a separate thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        logger.info("Scheduler started")
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        # Clear all scheduled jobs
        schedule.clear()
        logger.info("Scheduler stopped")
    
    def get_companies(self):
        """Get the current list of companies"""
        return self.scraper.get_companies()
    
    def get_company_names(self):
        """Get just the names of companies for UI display"""
        return self.scraper.get_company_names()


# For testing as standalone
if __name__ == "__main__":
    scheduler = SchedulerManager()
    # Update every 5 minutes for testing
    scheduler.start_scheduler('5m')
    
    try:
        # Run for an hour
        time.sleep(3600)
    except KeyboardInterrupt:
        scheduler.stop_scheduler()
        print("Scheduler stopped")