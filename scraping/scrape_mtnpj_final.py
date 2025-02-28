#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import sys
import re
import uuid
import time
import os
import logging
import argparse
import datetime
from pathlib import Path
import hashlib

# --- Selenium Imports ---
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException

# --- Global Login Credentials & Cookie File ---
# Credentials are read from environment variables.
LOGIN_EMAIL = os.environ.get("MP_LOGIN_EMAIL")
LOGIN_PASSWORD = os.environ.get("MP_LOGIN_PASSWORD")
COOKIE_FILE = "cookies.json"

# Define output and cache directory constants
OUTPUT_DIR = "data"  # or use absolute path like os.path.join(os.path.dirname(__file__), "data")
CACHE_DIR = os.path.join(OUTPUT_DIR, "cache")
CACHE_EXPIRY_DAYS = 7  # Cache entries older than this will be refreshed

# Global selenium driver for reuse
global_driver = None

# --- Logging Setup ---
def setup_logging(verbose=False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

# --- Caching Functions ---
def get_cache_key(url):
    """Generate a cache key from a URL"""
    return hashlib.md5(url.encode()).hexdigest()

def get_cache_path(url, data_type="html"):
    """Get the path where the cached file should be stored"""
    cache_key = get_cache_key(url)
    cache_dir = os.path.join(CACHE_DIR, data_type)
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f"{cache_key}.json")

def get_from_cache(url, data_type="html"):
    """Retrieve content from cache if it exists and is not expired"""
    cache_path = get_cache_path(url, data_type)
    
    if not os.path.exists(cache_path):
        return None
        
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
            
        # Check if cache is expired
        timestamp = datetime.datetime.fromisoformat(cache_data['timestamp'])
        now = datetime.datetime.now()
        if (now - timestamp).days > CACHE_EXPIRY_DAYS:
            logging.debug(f"Cache expired for {url}")
            return None
            
        logging.debug(f"Cache hit for {url}")
        return cache_data['content']
    except Exception as e:
        logging.warning(f"Error reading cache for {url}: {e}")
        return None

def save_to_cache(url, content, data_type="html"):
    """Save content to cache with current timestamp"""
    cache_path = get_cache_path(url, data_type)
    
    try:
        cache_data = {
            'url': url,
            'timestamp': datetime.datetime.now().isoformat(),
            'content': content
        }
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False)
            
        logging.debug(f"Saved to cache: {url}")
    except Exception as e:
        logging.warning(f"Error saving to cache for {url}: {e}")

# ==================== Helper Functions ====================

def get_soup(url):
    """Get BeautifulSoup object from URL with caching"""
    # Check cache first
    cached_html = get_from_cache(url, "html")
    if cached_html:
        return BeautifulSoup(cached_html, 'lxml')  # Using lxml parser for better performance
    
    try:
        logging.debug(f"Fetching {url}")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Save to cache
        save_to_cache(url, response.text, "html")
        
        return BeautifulSoup(response.text, 'lxml')
    except requests.RequestException as e:
        logging.error(f"Request error: {e}")
        return None

def get_current_area_name(soup):
    h1 = soup.find('h1')
    return h1.text.strip() if h1 else 'Unknown Area'

def get_sub_area_links(soup):
    """Get sub-area links from the area navigation section"""
    # Look for the specific area navigation div
    nav_div = soup.find('div', class_='max-height max-height-md-0 max-height-xs-400')
    if nav_div:
        # Find all area links within this section
        return nav_div.find_all('a', href=lambda x: x and '/area/' in x)
    return []

def is_lowest_level_area(soup, sub_areas):
    """Check if this is a lowest-level area (has routes but no sub-areas)"""
    # Check if there are any route links
    route_table = soup.find('table', {'id': 'left-nav-route-table'})
    has_routes = bool(route_table and route_table.find_all('a', href=lambda x: x and '/route/' in x))
    
    # Check if there are any sub-area links
    has_sub_areas = bool(sub_areas)
    
    # It's a lowest level area if it has routes but no sub-areas
    return has_routes and not has_sub_areas

def clean_area_name_from_url(url):
    last_segment = url.rstrip('/').split('/')[-1]
    return last_segment.replace('-', ' ').title()

def get_area_page_info(soup):
    page_views = "N/A"
    shared_date = "N/A"
    table = soup.find("table", class_="description-details")
    if table:
        rows = table.find_all("tr")
        for row in rows:
            header = row.find("td")
            if header:
                header_text = header.get_text(strip=True)
                if "Page Views:" in header_text:
                    value_cell = header.find_next_sibling("td")
                    if value_cell:
                        text = value_cell.get_text(" ", strip=True)
                        m = re.search(r'([\d,]+)', text)
                        if m:
                            page_views = m.group(1).replace(",", "")
                elif "Shared By:" in header_text:
                    value_cell = header.find_next_sibling("td")
                    if value_cell:
                        text = value_cell.get_text(" ", strip=True)
                        m = re.search(r'on\s+([A-Za-z]{3})\s+\d{1,2},\s*(\d{4})', text)
                        if m:
                            shared_date = f"{m.group(1)}, {m.group(2)}"
    return page_views, shared_date

def get_access_issues(soup):
    issue_divs = soup.find_all("div", id=re.compile("^access-details-"))
    issues = [div.get_text(separator=" ", strip=True) for div in issue_divs if div.get_text(strip=True)]
    return " ".join(issues) if issues else ""

def scrape_lowest_level_areas(start_url):
    """Find all lowest-level areas using iteration instead of recursion"""
    to_visit = [(start_url, [])]  # Stack of (url, hierarchy) pairs
    lowest_level_urls = []
    visited = set()

    while to_visit:
        url, hierarchy = to_visit.pop()
        if url in visited:
            continue
            
        visited.add(url)
        logging.info(f"Visiting {url}")
        
        soup = get_soup(url)
        if not soup:
            continue
            
        current_area = get_current_area_name(soup)
        current_hierarchy = hierarchy + [current_area]
        sub_area_links = get_sub_area_links(soup)
        
        if is_lowest_level_area(soup, sub_area_links):
            lowest_level_urls.append(url)
        else:
            for link in sub_area_links:
                if '/area/' in link['href']:
                    sub_area_url = link['href'] if link['href'].startswith('http') else BASE_URL + link['href']
                    if sub_area_url not in visited:
                        to_visit.append((sub_area_url, current_hierarchy))
    
    return lowest_level_urls

# ==================== Selenium Driver Management ====================

def get_driver():
    """Get or create a Selenium WebDriver instance"""
    global global_driver
    
    if global_driver is not None:
        try:
            # Test if driver is still working
            global_driver.current_url
            logging.debug("Reusing existing WebDriver")
            return global_driver
        except Exception:
            logging.debug("Existing WebDriver not responsive, creating new one")
            if global_driver:
                try:
                    global_driver.quit()
                except:
                    pass
            global_driver = None
    
    global_driver = init_selenium_driver()
    return global_driver

def init_selenium_driver():
    """Initialize Selenium driver"""
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")  # Updated headless argument
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Detect Chrome binary location based on platform
        if sys.platform == "darwin":  # macOS
            if os.path.exists("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
                chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            else:
                logging.error("Chrome not found in default location")
                return None
        
        # Try to initialize driver
        try:
            service = Service()
            driver = webdriver.Chrome(service=service, options=chrome_options)
            logging.debug("Successfully initialized Chrome driver")
            return driver
        except Exception as e:
            logging.error(f"Error creating Chrome driver: {e}")
            # Fallback to local ChromeDriver
            try:
                service = Service(executable_path="/usr/local/bin/chromedriver")
                driver = webdriver.Chrome(service=service, options=chrome_options)
                logging.debug("Successfully initialized Chrome driver with local ChromeDriver")
                return driver
            except Exception as e2:
                logging.error(f"Error creating Chrome driver with local ChromeDriver: {e2}")
                return None
                
    except Exception as e:
        logging.error(f"Error initializing driver: {e}")
        return None

def cleanup_driver():
    """Clean up the global driver when done"""
    global global_driver
    if global_driver:
        try:
            global_driver.quit()
        except:
            pass
        global_driver = None

# ==================== Selenium Dynamic Content Scrapers ====================

def get_comments(page_url, user_email=None, user_pass=None, cookie_file="cookies.json"):
    """Get comments using Selenium with caching"""
    # Check cache first
    cache_key = f"comments_{get_cache_key(page_url)}"
    cached_comments = get_from_cache(page_url, "comments")
    if cached_comments:
        return cached_comments
    
    try:
        driver = get_driver()
        if not driver:
            return []
            
        try:
            logging.debug(f"Fetching comments from {page_url}")
            driver.get(page_url)
            time.sleep(3)  # Wait for page load
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            # Try to find and click "show more comments" button
            try:
                load_more = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button.show-more-comments-trigger"))
                )
                load_more.click()
                time.sleep(2)
            except:
                pass  # No "show more" button or already showing all comments
            
            # Parse comments from the page source
            soup = BeautifulSoup(driver.page_source, "lxml")
            comments = []
            comment_list = soup.find("div", class_="comment-list")
            
            if comment_list:
                comment_elements = comment_list.find_all("table", class_="main-comment")
                for element in comment_elements:
                    bio_div = element.find("div", class_="bio")
                    comment_author = "N/A"
                    if bio_div:
                        a_tag = bio_div.find("a", href=re.compile(r"/user/"))
                        if a_tag:
                            comment_author = a_tag.text.strip()
                    
                    comment_body = element.find("div", class_="comment-body")
                    comment_text = comment_body.get_text(separator=" ", strip=True) if comment_body else "N/A"
                    
                    time_tag = element.find("span", class_="comment-time")
                    comment_time = time_tag.get_text(separator=" ", strip=True) if time_tag else "N/A"
                    
                    comments.append({
                        "comment_author": comment_author,
                        "comment_text": comment_text,
                        "comment_time": comment_time
                    })
            
            # Save to cache
            save_to_cache(page_url, comments, "comments")
            
            return comments
            
        except Exception as e:
            logging.error(f"Error processing comments: {e}")
            return []
            
    except Exception as e:
        logging.error(f"Error getting comments: {e}")
        return []

def parse_stats(soup):
    """Parse stats from BeautifulSoup object"""
    suggested_ratings = {}
    tick_comments = ""
    
    try:
        # Find Suggested Ratings table
        h3_suggested = None
        for h3 in soup.find_all("h3"):
            if re.search(r"^Suggested Ratings", h3.get_text(strip=True)):
                h3_suggested = h3
                break
                
        if h3_suggested:
            table = h3_suggested.find_next("table", class_="table table-striped")
            if table:
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) >= 2:
                        rating = cells[1].get_text(strip=True)
                        if rating and not rating.startswith('·'):  # Skip non-grade cells
                            suggested_ratings[rating] = suggested_ratings.get(rating, 0) + 1
                            
        # Find Ticks table
        h3_ticks = None
        for h3 in soup.find_all("h3"):
            if re.search(r"^Ticks", h3.get_text(strip=True)):
                h3_ticks = h3
                break
                
        if h3_ticks:
            table = h3_ticks.find_next("table", class_="table table-striped")
            if table:
                rows = table.find_all("tr")
                tick_list = []
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) >= 2:
                        tick_text = cells[1].get_text(" ", strip=True)
                        # Clean up the comment
                        tick_text = re.sub(r'\b[A-Za-z]{3}\s+\d{1,2},\s*\d{4}\b', '', tick_text)  # Remove date
                        tick_text = re.sub(r'·.*?·', '', tick_text)  # Remove climb type
                        tick_text = re.sub(r'\s+', ' ', tick_text).strip()
                        # Only include comments with 15 or more words
                        if tick_text and len(tick_text.split()) >= 15:
                            tick_list.append(tick_text)
                            
                tick_comments = " ".join(tick_list)
                
    except Exception as e:
        logging.error(f"Error parsing stats: {e}")
        
    return suggested_ratings, None, tick_comments

def get_route_stats(route_url):
    """Get route statistics using Selenium with caching"""
    # Check cache first
    cached_stats = get_from_cache(route_url, "stats")
    if cached_stats:
        return cached_stats.get("suggested_ratings", {}), None, cached_stats.get("tick_comments", "")
    
    try:
        stats_url = route_url.replace("/route/", "/route/stats/", 1)
        logging.debug(f"Fetching stats from {stats_url}")
        
        driver = get_driver()
        if not driver:
            return {}, None, ""
            
        driver.get(stats_url)
        time.sleep(1)  # Wait for page load
        
        content = driver.page_source
        soup = BeautifulSoup(content, "lxml")
        suggested_ratings, _, tick_comments = parse_stats(soup)
        
        # Save to cache
        stats_data = {
            "suggested_ratings": suggested_ratings,
            "tick_comments": tick_comments
        }
        save_to_cache(route_url, stats_data, "stats")
        
        return suggested_ratings, None, tick_comments
        
    except Exception as e:
        logging.error(f"Error getting route stats: {e}")
        return {}, None, ""

def get_area_comments(area_url, user_email=None, user_pass=None, cookie_file="cookies.json"):
    return get_comments(area_url, user_email=user_email, user_pass=user_pass, cookie_file=cookie_file)

# ==================== Route Details & Area Routes ====================

def get_route_details(route_url):
    """Get route details with caching"""
    # Check cache first
    cached_details = get_from_cache(route_url, "route_details")
    if cached_details:
        return cached_details
    
    response = requests.get(route_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    
    route_details = {}
    
    # Get route name from URL to find matching tr element
    route_id = route_url.split('/')[-1]
    
    # Find the route's tr element using the TODO-MARKER
    route_tr = soup.find('tr', id=lambda x: x and f'TODO-MARKER-{route_id}' in x)
    if route_tr:
        # Get left-to-right order
        route_lr = route_tr.get('data-lr')
        route_details['route_lr'] = int(route_lr) if route_lr else None
    else:
        route_details['route_lr'] = None
    
    # Route Grade (remove trailing "YDS")
    grade_element = soup.select_one('.rateYDS, .route-type.Ice')
    if grade_element:
        grade_full = grade_element.get_text(strip=True)
        grade = grade_full.split()[0].replace("YDS", "").strip()
        route_details['route_grade'] = grade
        # Extract protection grading from the parent h2 and store in route_protection_grading
        h2_element = grade_element.find_parent("h2")
        protection_grading = ""
        if h2_element:
            # Iterate over direct text nodes in the h2 element (ignoring child elements)
            for item in h2_element.contents:
                if isinstance(item, str):
                    text = item.strip()
                    if text:
                        protection_grading += text + " "
            route_details['route_protection_grading'] = protection_grading.strip()
        else:
            route_details['route_protection_grading'] = ""
    else:
        route_details['route_grade'] = 'Unknown'
        route_details['route_protection_grading'] = ""
    
    # Route Stars and Votes
    stars_avg_tag = soup.find('span', id=re.compile(r'starsWithAvgText'))
    if stars_avg_tag:
        stars_avg_text = stars_avg_tag.get_text(strip=True)
        stars_match = re.search(r'Avg: (\d+(\.\d+)?)', stars_avg_text)
        votes_match = re.search(r'from ([\d,]+)', stars_avg_text)
        route_details['route_stars'] = float(stars_match.group(1)) if stars_match else 'N/A'
        route_details['route_votes'] = int(votes_match.group(1).replace(',', '')) if votes_match else 'N/A'
    else:
        route_details['route_stars'] = 'N/A'
        route_details['route_votes'] = 'N/A'
    
    # Route Type, Pitches, and Length; split length into two fields and extract pitch count
    type_length_tag = soup.find(string='Type:')
    if type_length_tag:
        type_length = type_length_tag.find_next('td').get_text(strip=True)
        type_length_split = type_length.split(',')
        types = []
        length_str = None
        route_pitches = None  # We'll store the pitch count as an integer here.
        for item in type_length_split:
            item = item.strip()
            # Check for a pitch count pattern, e.g., "10 pitches"
            pitch_match = re.search(r'(\d+)\s*pitches?', item, re.IGNORECASE)
            if pitch_match:
                route_pitches = int(pitch_match.group(1))
                # Do not add this item to the route type list.
            elif re.search(r'\d+\s*ft', item, re.IGNORECASE):
                length_str = item
            else:
                types.append(item)
        route_details['route_type'] = ', '.join(types)
        # If no pitch count was found, assume a single-pitch route.
        if route_pitches is None:
            route_pitches = 1
        route_details['route_pitches'] = route_pitches
        if length_str:
            m = re.search(r'(\d+)\s*ft\s*\((\d+)\s*m\)', length_str)
            if m:
                route_details['route_length_ft'] = int(m.group(1))
                route_details['route_length_meter'] = int(m.group(2))
            else:
                route_details['route_length_ft'] = None
                route_details['route_length_meter'] = None
        else:
            route_details['route_length_ft'] = None
            route_details['route_length_meter'] = None
    else:
        route_details['route_type'] = 'N/A'
        route_details['route_length_ft'] = None
        route_details['route_length_meter'] = None
        route_details['route_pitches'] = 1
    
    # Route FA (First Ascent)
    fa_tag = soup.find(string='FA:')
    if fa_tag:
        route_details['route_fa'] = fa_tag.find_next('td').get_text(strip=True)
    else:
        route_details['route_fa'] = 'N/A'
    
    # Route Description, Location, and Protection
    route_description, route_location, route_protection = 'N/A', 'N/A', 'N/A'
    for h2_tag in soup.find_all('h2'):
        text = h2_tag.get_text()
        if "Description" in text:
            description_div = h2_tag.find_next('div', {'class': 'fr-view'})
            route_description = description_div.get_text(strip=True) if description_div else 'N/A'
        elif "Location" in text:
            location_div = h2_tag.find_next('div', {'class': 'fr-view'})
            route_location = location_div.get_text(strip=True) if location_div else 'N/A'
        elif "Protection" in text:
            protection_div = h2_tag.find_next('div', {'class': 'fr-view'})
            route_protection = protection_div.get_text(strip=True) if protection_div else 'N/A'
        elif "Gear" in text:
            gear_div = h2_tag.find_next('div', {'class': 'fr-view'})
            route_protection = gear_div.get_text(strip=True) if gear_div else 'N/A'
    
    route_details['route_description'] = route_description
    route_details['route_location'] = route_location
    route_details['route_protection'] = route_protection

    # Extract route page views and shared date using the same helper.
    route_page_views, route_shared_on = get_area_page_info(soup)
    route_details['route_page_views'] = route_page_views
    route_details['route_shared_on'] = route_shared_on

    # Unique ID for the route
    route_details['route_id'] = str(uuid.uuid4())
    
    # Add empty tag arrays
    route_details['route_tags'] = []
    route_details['route_composite_tags'] = []
    
    # Scrape route comments dynamically
    route_details['route_comments'] = get_comments(route_url, user_email=LOGIN_EMAIL, user_pass=LOGIN_PASSWORD, cookie_file=COOKIE_FILE)
    
    # Fetch route stats: suggested ratings and tick comments.
    suggested_ratings, _, tick_comments = get_route_stats(route_url)
    route_details['route_suggested_ratings'] = suggested_ratings
    route_details['route_tick_comments'] = tick_comments
    
    # Save to cache
    save_to_cache(route_url, route_details, "route_details")
    
    return route_details

def get_routes(area_url):
    """Get routes with caching"""
    # Check cache first
    cached_area = get_from_cache(area_url, "area")
    if cached_area:
        return cached_area
        
    response = requests.get(area_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'lxml')
    
    area_name = area_url.rstrip('/').split('/')[-1]
    description_div = soup.find('div', {'class': 'fr-view'})
    area_description = description_div.get_text(strip=True) if description_div else 'N/A'
    
    area_getting_there = 'N/A'
    for h2_tag in soup.find_all('h2'):
        if "Getting There" in h2_tag.get_text():
            getting_there_div = h2_tag.find_next('div', {'class': 'fr-view'})
            area_getting_there = getting_there_div.get_text(strip=True) if getting_there_div else 'N/A'
            break

    area_gps = 'N/A'
    for tr in soup.find_all('tr'):
        if "GPS:" in tr.get_text():
            gps_tag = tr.find('a', {'target': '_blank', 'href': True})
            if gps_tag and 'maps.google.com' in gps_tag['href']:
                area_gps = gps_tag['href']
                break

    area_access_issues = get_access_issues(soup)
    area_page_views, area_shared_on = get_area_page_info(soup)
    
    area_hierarchy = []
    breadcrumb_div = soup.find('div', class_='mb-half small text-warm')
    if breadcrumb_div:
        links = breadcrumb_div.find_all('a')
        for idx, link in enumerate(links):
            raw_name = link.get_text(strip=True)
            cleaned_name = clean_area_name_from_url(link['href']) if (not raw_name or raw_name.endswith('…') or len(raw_name) < 5) else raw_name
            area_hierarchy.append({
                "level": idx + 1,
                "area_hierarchy_name": cleaned_name,
                "area_hierarchy_url": link['href']
            })
        
        # Add current area as the lowest level
        current_area_name = clean_area_name_from_url(area_url)
        area_hierarchy.append({
            "level": len(area_hierarchy) + 1,
            "area_hierarchy_name": current_area_name,
            "area_hierarchy_url": area_url
        })

    area_comments = get_area_comments(area_url, user_email=LOGIN_EMAIL, user_pass=LOGIN_PASSWORD, cookie_file=COOKIE_FILE)
    
    routes = []
    route_table = soup.find('table', {'id': 'left-nav-route-table'})
    if route_table:
        route_elements = route_table.find_all('tr')
        valid_route_elements = [elem for elem in route_elements if elem.find('a')]
        total_routes = len(valid_route_elements)
        for idx, route_element in enumerate(valid_route_elements, start=1):
            logging.info(f"    Scraping route {idx}/{total_routes}...")
            link_tag = route_element.find('a')
            if link_tag:
                route_url = link_tag['href']
                if not route_url.startswith('http'):
                    route_url = BASE_URL + route_url
                route_name = link_tag.get_text(strip=True)
                
                # Get left-to-right order and ensure it's an integer
                route_lr = route_element.get('data-lr')
                route_lr = int(route_lr) if route_lr is not None else 0
                
                # Get route details first
                route_details = get_route_details(route_url)
                
                # Create final route data, ensuring route_lr is set
                ordered_route = {
                    "route_name": route_name, 
                    "route_url": route_url,
                    "route_lr": route_lr
                }
                
                # Update with other details, but preserve route_lr
                if route_details:
                    route_details['route_lr'] = route_lr  # Ensure route_lr is preserved
                    ordered_route.update(route_details)
                
                routes.append(ordered_route)
    
    area_data = {
        "area_id": str(uuid.uuid4()),
        "area_url": area_url,
        "area_name": area_name,
        "area_gps": area_gps,
        "area_description": area_description,
        "area_getting_there": area_getting_there,
        "area_tags": [],
        "area_hierarchy": area_hierarchy,
        "area_access_issues": area_access_issues,
        "area_page_views": area_page_views,
        "area_shared_on": area_shared_on,
        "area_comments": area_comments,
        "routes": routes
    }
    
    # Save to cache
    save_to_cache(area_url, area_data, "area")
    
    return area_data

def safe_get_routes(url, retries=3, delay=5):
    for attempt in range(1, retries + 1):
        try:
            return get_routes(url)
        except Exception as e:
            logging.error(f"Error processing {url} (attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                logging.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logging.error("All retry attempts failed.")
    return None

def get_output_filename(base_url):
    """Generate output filename from base URL"""
    area_name = base_url.rstrip('/').split('/')[-1]
    return os.path.join(OUTPUT_DIR, f"{area_name}_routes.json")

def save_all_areas(all_areas, base_url):
    """Save all areas to a single JSON file"""
    try:
        output_file = get_output_filename(base_url)
        # Create output directory if it doesn't exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Save to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_areas, f, indent=2, ensure_ascii=False)
        logging.info(f"All data saved to {output_file}")
    except Exception as e:
        logging.error(f"Error saving data: {e}")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Scrape Mountain Project routes')
    parser.add_argument('url', help='Base URL to scrape')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--cache-days', type=int, default=7, help='Cache expiry in days')
    parser.add_argument('--no-cache', action='store_true', help='Disable caching')
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Set cache expiry
    global CACHE_EXPIRY_DAYS
    CACHE_EXPIRY_DAYS = 0 if args.no_cache else args.cache_days
    
    if not args.url:
        logging.error("Please provide area URL as argument")
        sys.exit(1)
        
    BASE_URL = args.url
    logging.info(f"Finding all lowest-level areas in {BASE_URL}...")
    sys.setrecursionlimit(10000)  # Increase limit to 10000
    lowest_level_urls = scrape_lowest_level_areas(BASE_URL)
    logging.info(f"Found {len(lowest_level_urls)} lowest-level areas")
    
    all_areas = []
    try:
        for i, url in enumerate(lowest_level_urls, 1):
            logging.info(f"Processing area {i}/{len(lowest_level_urls)}...")
            try:
                area_data = safe_get_routes(url, retries=3, delay=5)
                if area_data:
                    all_areas.append(area_data)
                else:
                    logging.warning(f"Skipping {url} after failed attempts")
            except Exception as e:
                logging.error(f"Error processing {url}: {e}")
        
        # Save all areas to one file
        save_all_areas(all_areas, BASE_URL)
    finally:
        # Clean up resources
        cleanup_driver()

if __name__ == "__main__":
    main()