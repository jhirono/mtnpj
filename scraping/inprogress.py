import asyncio
import aiohttp
from bs4 import BeautifulSoup
import json
import logging
from typing import List, Dict, Optional, Set
from pathlib import Path
import re
from urllib.parse import urljoin
import uuid
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MountainProjectScraper:
    def __init__(self, email: Optional[str] = None, password: Optional[str] = None):
        self.base_url = "https://www.mountainproject.com"
        self.email = email
        self.password = password
        self.session = None
        self.is_authenticated = False
        self.rate_limit_delay = 1.0
        self.visited_urls: Set[str] = set()

    async def init_session(self):
        """Initialize session and handle login if credentials provided"""
        self.session = aiohttp.ClientSession(
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        if self.email and self.password:
            await self.login()

    async def login(self) -> bool:
        """Handle Mountain Project login"""
        try:
            login_url = f"{self.base_url}/auth/login"
            async with self.session.get(login_url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                csrf_token = soup.find('input', {'name': '_token'})['value']

            login_data = {
                'email': self.email,
                'password': self.password,
                '_token': csrf_token
            }
            async with self.session.post(login_url, data=login_data) as response:
                self.is_authenticated = response.status == 200
                logger.info(f"Login {'successful' if self.is_authenticated else 'failed'}")
                return self.is_authenticated
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    async def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a page with rate limiting"""
        if url in self.visited_urls:
            logger.debug(f"Skipping already visited URL: {url}")
            return None
            
        try:
            await asyncio.sleep(self.rate_limit_delay)
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    self.visited_urls.add(url)
                    return BeautifulSoup(html, 'html.parser')
                logger.error(f"Failed to fetch {url}: {response.status}")
                return None
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def _get_area_name(self, soup: BeautifulSoup) -> str:
        """Extract area name from the page"""
        h1 = soup.find('h1')
        return h1.text.strip() if h1 else ""

    def _get_description(self, soup: BeautifulSoup) -> str:
        """Extract area description"""
        description_header = soup.find('h2', string='Description')
        if description_header:
            description_div = description_header.find_next('div', class_='fr-view')
            return description_div.text.strip() if description_div else ""
        return ""

    def _get_getting_there(self, soup: BeautifulSoup) -> str:
        """Extract getting there information"""
        getting_there_header = soup.find('h2', string='Getting There')
        if getting_there_header:
            getting_there_div = getting_there_header.find_next('div', class_='fr-view')
            return getting_there_div.text.strip() if getting_there_div else ""
        return ""

    def _extract_sub_areas(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract sub-areas from an area page"""
        sub_areas = []
        left_nav_div = soup.find('div', class_='mp-sidebar')
        if left_nav_div:
            area_links = left_nav_div.find_all('a', href=re.compile(r'/area/\d+/'))
            for link in area_links:
                sub_areas.append({
                    "name": link.text.strip(),
                    "url": urljoin(self.base_url, link['href'])
                })
        return sub_areas

    def _extract_routes_table(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract routes from the routes table"""
        routes = []
        routes_table = soup.find('table', {'id': 'left-nav-route-table'})
        if routes_table:
            for row in routes_table.find_all('tr')[1:]:  # Skip header row
                link = row.find('a')
                if link:
                    routes.append({
                        "name": link.text.strip(),
                        "url": urljoin(self.base_url, link['href'])
                    })
        return routes

    def _extract_grade(self, soup: BeautifulSoup) -> str:
        """Extract route grade"""
        grade_div = soup.find('h2', class_='inline')
        if grade_div:
            grade_text = grade_div.text.strip()
            grade_match = re.search(r'5\.\d+[abcd]?[+-]?', grade_text)
            return grade_match.group(0) if grade_match else ""
        return ""

    def _extract_stars(self, soup: BeautifulSoup) -> float:
        """Extract route star rating"""
        stars_span = soup.find('span', class_='stars')
        if stars_span:
            stars = len(stars_span.find_all('img', alt='Star'))
            return float(stars)
        return 0.0

    def _extract_votes(self, soup: BeautifulSoup) -> int:
        """Extract number of votes"""
        votes_span = soup.find('span', string=re.compile(r'\d+\s+votes?'))
        if votes_span:
            votes_match = re.search(r'(\d+)', votes_span.text)
            return int(votes_match.group(1)) if votes_match else 0
        return 0

    def _extract_type_info(self, soup: BeautifulSoup) -> Dict:
        """Extract route type information"""
        info = {
            "route_type": "",
            "route_length_ft": None,
            "route_length_meter": None,
            "route_pitches": 1
        }
        
        type_row = soup.find('tr', string=re.compile('Type:'))
        if type_row:
            type_cell = type_row.find('td')
            if type_cell:
                type_text = type_cell.text.strip()
                
                # Extract length
                length_match = re.search(r'(\d+)\s*ft(?:\s*\((\d+)\s*m\))?', type_text)
                if length_match:
                    info["route_length_ft"] = int(length_match.group(1))
                    if length_match.group(2):
                        info["route_length_meter"] = int(length_match.group(2))

                # Extract pitches
                pitch_match = re.search(r'(\d+)\s*pitch', type_text, re.IGNORECASE)
                if pitch_match:
                    info["route_pitches"] = int(pitch_match.group(1))

                # Extract type
                type_parts = [p.strip() for p in type_text.split(',')]
                types = []
                for part in type_parts:
                    if not re.search(r'(\d+\s*ft|\d+\s*pitch)', part, re.IGNORECASE):
                        types.append(part.strip())
                info["route_type"] = ', '.join(t for t in types if t)

        return info

    def _get_route_description(self, soup: BeautifulSoup) -> str:
        """Extract route description"""
        desc_header = soup.find('h2', string='Description')
        if desc_header:
            desc_div = desc_header.find_next('div', class_='fr-view')
            return desc_div.text.strip() if desc_div else ""
        return ""

    def _get_route_location(self, soup: BeautifulSoup) -> str:
        """Extract route location"""
        loc_header = soup.find('h2', string='Location')
        if loc_header:
            loc_div = loc_header.find_next('div', class_='fr-view')
            return loc_div.text.strip() if loc_div else ""
        return ""

    def _get_route_protection(self, soup: BeautifulSoup) -> str:
        """Extract route protection information"""
        prot_header = soup.find('h2', string='Protection')
        if prot_header:
            prot_div = prot_header.find_next('div', class_='fr-view')
            return prot_div.text.strip() if prot_div else ""
        return ""

    def _get_first_ascent(self, soup: BeautifulSoup) -> str:
        """Extract first ascent information"""
        fa_row = soup.find('tr', string=re.compile('FA:'))
        if fa_row:
            fa_cell = fa_row.find('td')
            return fa_cell.text.strip() if fa_cell else ""
        return ""

    def _extract_suggested_ratings(self, soup: BeautifulSoup) -> Dict[str, int]:
        """Extract suggested ratings from stats page"""
        ratings = {}
        table = soup.find('table', class_='table table-striped')
        if table:
            for row in table.find_all('tr')[1:]:  # Skip header
                cols = row.find_all('td')
                if len(cols) >= 2:
                    grade = cols[0].text.strip()
                    count = int(cols[1].text.strip())
                    ratings[grade] = count
        return ratings

    def _extract_tick_comments(self, soup: BeautifulSoup) -> str:
        """Extract tick comments from stats page"""
        comments_div = soup.find('div', id='route-tick-comments')
        return comments_div.text.strip() if comments_div else ""

    async def scrape_area(self, url: str) -> Dict:
        """Scrape an area and all its sub-areas"""
        soup = await self.get_page(url)
        if not soup:
            return {}

        area_data = {
            "area_id": self._extract_id_from_url(url),
            "area_url": url,
            "area_name": self._get_area_name(soup),
            "area_description": self._get_description(soup),
            "area_getting_there": self._get_getting_there(soup),
            "sub_areas": [],
            "routes": []
        }

        # Check for sub-areas
        sub_areas = self._extract_sub_areas(soup)
        if sub_areas:
            # This is a parent area, recursively scrape sub-areas
            for sub_area in sub_areas:
                sub_area_data = await self.scrape_area(sub_area["url"])
                if sub_area_data:
                    area_data["sub_areas"].append(sub_area_data)
        else:
            # This is a leaf area, extract routes
            routes = self._extract_routes_table(soup)
            for route in routes:
                route_data = await self.scrape_route(route["url"])
                if route_data:
                    area_data["routes"].append(route_data)

        return area_data

    async def scrape_route(self, url: str) -> Dict:
        """Scrape complete route information"""
        soup = await self.get_page(url)
        if not soup:
            return {}

        route_data = {
            "route_id": self._extract_id_from_url(url),
            "route_url": url,
            "route_name": self._get_area_name(soup),  # Reuse area name extraction
            "route_grade": self._extract_grade(soup),
            "route_stars": self._extract_stars(soup),
            "route_votes": self._extract_votes(soup),
            "route_description": self._get_route_description(soup),
            "route_location": self._get_route_location(soup),
            "route_protection": self._get_route_protection(soup),
            "route_fa": self._get_first_ascent(soup)
        }

        # Extract type info
        type_info = self._extract_type_info(soup)
        route_data.update(type_info)

        # Get stats if authenticated
        if self.is_authenticated:
            stats = await self._get_route_stats(url)
            route_data.update(stats)

        return route_data

    async def _get_route_stats(self, route_url: str) -> Dict:
        """Get route statistics from the stats page"""
        stats_url = route_url.replace("/route/", "/route/stats/")
        soup = await self.get_page(stats_url)
        if not soup:
            return {}

        return {
            "route_suggested_ratings": self._extract_suggested_ratings(soup),
            "route_tick_comments": self._extract_tick_comments(soup)
        }

    def _extract_id_from_url(self, url: str) -> str:
        """Extract the numeric ID from a Mountain Project URL"""
        match = re.search(r'/(\d+)/', url)
        return match.group(1) if match else str(uuid.uuid4())

    def save_to_json(self, data: Dict, filename: str):
        """Save scraped data to a JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

async def main():
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python3 inprogress.py <mountain_project_url>")
        print("Example: python3 inprogress.py https://www.mountainproject.com/area/105790784/castle-rock")
        sys.exit(1)

    url = sys.argv[1]
    if not url.startswith("https://www.mountainproject.com/area/"):
        print("Error: URL must be a Mountain Project area URL")
        print("Example: https://www.mountainproject.com/area/105790784/castle-rock")
        sys.exit(1)

    # Get credentials from environment variables
    email = os.getenv("MP_LOGIN_EMAIL")
    password = os.getenv("MP_LOGIN_PASSWORD")
    
    if not email or not password:
        logger.warning("No credentials found. Set MP_LOGIN_EMAIL and MP_LOGIN_PASSWORD environment variables for authenticated access.")
    
    # Initialize scraper
    scraper = MountainProjectScraper(email, password)
    await scraper.init_session()
    
    try:
        # Start scraping from provided URL
        area_data = await scraper.scrape_area(url)
        
        if not area_data:
            logger.error("Failed to scrape data from the provided URL")
            sys.exit(1)
            
        # Save the results
        area_name = area_data.get("area_name", "area").lower().replace(" ", "-")
        output_file = f"{area_name}_routes.json"
        scraper.save_to_json(area_data, output_file)
        logger.info(f"Data saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if scraper.session:
            await scraper.session.close()

if __name__ == "__main__":
    asyncio.run(main())