#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import sys
import re
import uuid
import time
import os

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

# ==================== Helper Functions ====================

def get_soup(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return None

def get_current_area_name(soup):
    h1 = soup.find('h1')
    return h1.text.strip() if h1 else 'Unknown Area'

def get_sub_area_links(soup):
    sub_areas_div = soup.find('div', class_='max-height max-height-md-0 max-height-xs-400')
    return sub_areas_div.find_all('a', href=True) if sub_areas_div else []

def is_lowest_level_area(sub_areas):
    return not any('/area/' in link['href'] for link in sub_areas)

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

def scrape_lowest_level_areas(url, hierarchy=None, lowest_level_urls=None):
    if hierarchy is None:
        hierarchy = []
    if lowest_level_urls is None:
        lowest_level_urls = []
    soup = get_soup(url)
    if soup is None:
        return lowest_level_urls
    current_area = get_current_area_name(soup)
    hierarchy.append(current_area)
    sub_area_links = get_sub_area_links(soup)
    if is_lowest_level_area(sub_area_links):
        lowest_level_urls.append(url)
    else:
        for link in sub_area_links:
            if '/area/' in link['href']:
                sub_area_url = link['href'] if link['href'].startswith('http') else BASE_URL + link['href']
                scrape_lowest_level_areas(sub_area_url, hierarchy[:], lowest_level_urls)
    return lowest_level_urls

# ==================== Selenium Dynamic Comment Scrapers ====================

def get_comments(page_url, user_email=None, user_pass=None, cookie_file="cookies.json"):
    """Get comments using Selenium"""
    try:
        driver = init_selenium_driver()
        if not driver:
            return []
            
        try:
            driver.get(page_url)
            time.sleep(3)
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
            soup = BeautifulSoup(driver.page_source, "html.parser")
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
            
            return comments
            
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"Error getting comments: {e}")
        return []

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
                print("Chrome not found in default location")
                return None
        
        # Try to initialize driver
        try:
            service = Service()
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("Successfully initialized Chrome driver")
            return driver
        except Exception as e:
            print(f"Error creating Chrome driver: {e}")
            # Fallback to local ChromeDriver
            try:
                service = Service(executable_path="/usr/local/bin/chromedriver")
                driver = webdriver.Chrome(service=service, options=chrome_options)
                print("Successfully initialized Chrome driver with local ChromeDriver")
                return driver
            except Exception as e2:
                print(f"Error creating Chrome driver with local ChromeDriver: {e2}")
                return None
                
    except Exception as e:
        print(f"Error initializing driver: {e}")
        return None

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
                        if tick_text:
                            tick_list.append(tick_text)
                            
                tick_comments = " ".join(tick_list)
                
    except Exception as e:
        print(f"Error parsing stats: {e}")
        
    return suggested_ratings, None, tick_comments

def get_route_stats(route_url):
    """Get route statistics using Selenium"""
    try:
        stats_url = route_url.replace("/route/", "/route/stats/", 1)
        print(f"\nDEBUG: Fetching stats from {stats_url}")
        
        # Try simple request first
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(stats_url, headers=headers)
            response.raise_for_status()
            content = response.text
            if "Please Confirm" in content:
                raise Exception("Confirmation needed")
            soup = BeautifulSoup(content, "html.parser")
            return parse_stats(soup)
        except Exception:
            print("DEBUG: Simple request failed, trying with Selenium")
            
            # Fall back to Selenium
            driver = init_selenium_driver()
            if not driver:
                return {}, None, ""
                
            try:
                driver.get(stats_url)
                time.sleep(5)
                print("DEBUG: Initial page load complete")
                
                selenium_html = driver.page_source
                soup = BeautifulSoup(selenium_html, "html.parser")
                return parse_stats(soup)
            finally:
                driver.quit()
                
    except Exception as e:
        print(f"DEBUG: Error in get_route_stats: {e}")
        return {}, None, ""

def get_area_comments(area_url, user_email=None, user_pass=None, cookie_file="cookies.json"):
    return get_comments(area_url, user_email=user_email, user_pass=user_pass, cookie_file=cookie_file)

# ==================== Route Details & Area Routes ====================

def get_route_details(route_url):
    response = requests.get(route_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
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
        votes_match = re.search(r'from (\d+)', stars_avg_text)
        route_details['route_stars'] = float(stars_match.group(1)) if stars_match else 'N/A'
        route_details['route_votes'] = int(votes_match.group(1)) if votes_match else 'N/A'
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
    
    return route_details

def get_routes(area_url):
    response = requests.get(area_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
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
    
    area_comments = get_area_comments(area_url, user_email=LOGIN_EMAIL, user_pass=LOGIN_PASSWORD, cookie_file=COOKIE_FILE)
    
    routes = []
    route_table = soup.find('table', {'id': 'left-nav-route-table'})
    if route_table:
        route_elements = route_table.find_all('tr')
        valid_route_elements = [elem for elem in route_elements if elem.find('a')]
        total_routes = len(valid_route_elements)
        for idx, route_element in enumerate(valid_route_elements, start=1):
            print(f"    Scraping route {idx}/{total_routes}...")
            link_tag = route_element.find('a')
            if link_tag:
                route_url = link_tag['href']
                if not route_url.startswith('http'):
                    route_url = BASE_URL + route_url
                route_name = link_tag.get_text(strip=True)
                
                # Get left-to-right order
                route_lr = route_element.get('data-lr')
                route_lr = int(route_lr) if route_lr else None
                
                route_details = get_route_details(route_url)
                ordered_route = {
                    "route_name": route_name, 
                    "route_url": route_url,
                    "route_lr": route_lr  # Add route_lr to output
                }
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
    
    return area_data

def safe_get_routes(url, retries=3, delay=5):
    for attempt in range(1, retries + 1):
        try:
            return get_routes(url)
        except Exception as e:
            print(f"Error processing {url} (attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("All retry attempts failed.")
    return None

def save_urls_to_json(all_areas, base_url):
    area_name = base_url.split('/')[-1]
    file_name = f"{area_name}_routes.json"
    try:
        with open(file_name, 'w') as f:
            json.dump(all_areas, f, indent=4)
            print(f"Data saved to {file_name}")
    except IOError as e:
        print(f"Error saving data to {file_name}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 script.py 'base_url'")
        sys.exit(1)
    BASE_URL = sys.argv[1]
    lowest_level_urls = scrape_lowest_level_areas(BASE_URL)
    all_areas = []
    for index, url in enumerate(lowest_level_urls, start=1):
        try:
            print(f"Scraping {url} ({index}/{len(lowest_level_urls)})...")
            area_details = safe_get_routes(url, retries=3, delay=5)
            if area_details is not None:
                all_areas.append(area_details)
            else:
                print(f"Skipping {url} after failed attempts.")
        except Exception as e:
            print(f"Error processing {url}: {e}")
    save_urls_to_json(all_areas, BASE_URL)