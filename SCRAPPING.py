#step 1 scraping the data using selenium 

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
import pandas as pd
import re
import logging
import csv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='redbus_scraper.log'
)

class RedbusDetailedScraper:
    def __init__(self):
        self.firefox_options = Options()
        self.firefox_options.set_preference('permissions.default.image', 2)
        self.firefox_options.set_preference('general.useragent.override', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        self.driver = webdriver.Firefox(options=self.firefox_options)
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 30)
        self.govt_buses = []
        self.private_buses = []

    def scroll_page(self):
        """Scroll the page gradually to load all buses"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            for i in range(0, last_height, 200):
                self.driver.execute_script(f"window.scrollTo(0, {i});")
                time.sleep(0.2)
            
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

    def extract_text_safely(self, element, selectors):
        """Safely extract text from an element using multiple possible selectors"""
        for selector in selectors:
            try:
                result = element.find_element(By.CSS_SELECTOR, selector).text.strip()
                if result:
                    return result
            except:
                continue
        return ""

    def classify_bus_type(self, bus_type_text):
        """Classify bus type into categories"""
        bus_type = []
        if not bus_type_text:
            return "Not specified"
        
        if any(word in bus_type_text.lower() for word in ['sleeper', 'sleeping']):
            bus_type.append('Sleeper')
        if any(word in bus_type_text.lower() for word in ['seater', 'sitting']):
            bus_type.append('Seater')
        if 'ac' in bus_type_text.lower() or 'a/c' in bus_type_text.lower():
            bus_type.append('AC')
        if 'non ac' in bus_type_text.lower() or 'non-ac' in bus_type_text.lower():
            bus_type.append('Non-AC')
        
        return ' + '.join(bus_type) if bus_type else bus_type_text

    def extract_star_rating(self, rating_text):
        """Extract numerical star rating from text"""
        if not rating_text:
            return "No rating"
        try:
            rating_match = re.search(r'(\d+(\.\d+)?)', rating_text)
            if rating_match:
                return float(rating_match.group(1))
        except:
            pass
        return "No rating"

    def extract_seats_available(self, seats_text):
        """Extract number of available seats from text"""
        if not seats_text:
            return "Not specified"
        try:
            seats_match = re.search(r'(\d+)', seats_text)
            if seats_match:
                return int(seats_match.group(1))
        except:
            pass
        return "Not specified"

    def is_government_bus(self, bus_name):
        """Check if the bus is a government bus"""
        govt_keywords = [
            'KSRTC', 'TSRTC', 'APSRTC', 'MSRTC', 'GSRTC', 'TNSTC',
            'State', 'Government', 'Corporation'
        ]
        return any(keyword.lower() in bus_name.lower() for keyword in govt_keywords)

    def scrape_route(self, source, destination, date):
        """Scrape bus data for a specific route"""
        url = f"https://www.redbus.in/bus-tickets/{source}-to-{destination}?date={date}"
        logging.info(f"Scraping URL: {url}")
        
        try:
            self.driver.get(url)
            time.sleep(5)
            self.scroll_page()
            
            bus_items = self.driver.find_elements(By.CSS_SELECTOR, "div[class*='bus-item']")
            logging.info(f"Found {len(bus_items)} buses")
            
            for bus in bus_items:
                try:
                    bus_name = self.extract_text_safely(bus, [
                        "div[class*='travels']", 
                        ".travels-name", 
                        ".operator-text"
                    ])
                    
                    bus_type_text = self.extract_text_safely(bus, [
                        "div[class*='bus-type']",
                        ".bus-type-text",
                        ".type"
                    ])
                    
                    departure = self.extract_text_safely(bus, [
                        "div[class*='dep-time']",
                        ".departure-time",
                        ".time-text"
                    ])
                    
                    duration = self.extract_text_safely(bus, [
                        "div[class*='duration']",
                        ".duration-text",
                        ".dur"
                    ])
                    
                    arrival = self.extract_text_safely(bus, [
                        "div[class*='arr-time']",
                        ".arrival-time"
                    ])
                    
                    price = self.extract_text_safely(bus, [
                        "div[class*='fare']",
                        ".price",
                        ".fare-text"
                    ])
                    
                    rating_text = self.extract_text_safely(bus, [
                        "div[class*='rating']",
                        ".rating-text"
                    ])
                    
                    seats_text = self.extract_text_safely(bus, [
                        "div[class*='seats']",
                        ".seat-text"
                    ])
                    
                    if not bus_name:
                        continue
                    
                    bus_info = {
                        'route_name': f"{source.title()} to {destination.title()}",
                        'route_link': url,
                        'bus_name': bus_name,
                        'bus_type': self.classify_bus_type(bus_type_text),
                        'departing_time': departure,
                        'duration': duration,
                        'reaching_time': arrival,
                        'star_rating': self.extract_star_rating(rating_text),
                        'price': price.replace('₹', '').strip() if price else "Not specified",
                        'seats_available': self.extract_seats_available(seats_text),
                        'scrape_date': datetime.now().strftime('%Y-%m-%d'),
                        'bus_category': 'Government' if self.is_government_bus(bus_name) else 'Private'
                    }
                    
                    if self.is_government_bus(bus_name):
                        self.govt_buses.append(bus_info)
                        logging.info(f"Added government bus: {bus_name}")
                    else:
                        self.private_buses.append(bus_info)
                        logging.info(f"Added private bus: {bus_name}")
                    
                except Exception as e:
                    logging.error(f"Error scraping individual bus: {str(e)}")
                    continue
                
        except Exception as e:
            logging.error(f"Error scraping route {source} to {destination}: {str(e)}")

    def save_to_csv(self, filename="bus_data.csv"):
        """Save scraped data to CSV file"""
        # Combine both government and private buses
        all_buses = self.govt_buses + self.private_buses
        
        if not all_buses:
            logging.warning("No data to save!")
            return
        
        # Define CSV fields
        fields = [
            'bus_category',
            'route_name',
            'route_link',
            'bus_name',
            'bus_type',
            'departing_time',
            'duration',
            'reaching_time',
            'star_rating',
            'price',
            'seats_available',
            'scrape_date'
        ]
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fields)
                writer.writeheader()
                writer.writerows(all_buses)
            
            logging.info(f"Successfully saved data to {filename}")
            logging.info(f"Total records saved: {len(all_buses)}")
        except Exception as e:
            logging.error(f"Error saving to CSV: {str(e)}")

    def close(self):
        """Close the browser"""
        self.driver.quit()

def main():
    routes = [
        {'source': 'bangalore', 'destination': 'chennai'},
        {'source': 'bangalore', 'destination': 'mysore'},
        {'source': 'hyderabad', 'destination': 'bangalore'},
        {'source': 'chennai', 'destination': 'coimbatore'}
    ]
    
    scraper = RedbusDetailedScraper()
    tomorrow = (datetime.now() + pd.Timedelta(days=1)).strftime('%d-%m-%Y')
    
    try:
        for route in routes:
            logging.info(f"\nScraping route: {route['source']} to {route['destination']}")
            scraper.scrape_route(route['source'], route['destination'], tomorrow)
            time.sleep(10)
            
            if len(scraper.govt_buses) >= 10:
                break
        
        # Save the data to CSV instead of text file
        scraper.save_to_csv()
        
        logging.info(f"\nScraping completed!")
        logging.info(f"Total government buses found: {len(scraper.govt_buses)}")
        logging.info(f"Total private buses found: {len(scraper.private_buses)}")
        
    except Exception as e:
        logging.error(f"Main execution error: {str(e)}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()