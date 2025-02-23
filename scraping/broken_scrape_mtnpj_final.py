#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import json
import sys
import re
import uuid
import time
import os
from time import sleep
from random import uniform

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

# Add at the top level
driver = None

def init_selenium_driver():
    """Initialize Selenium driver with login"""
    global driver
    
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")  # Updated headless argument
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Add window size to ensure consistent rendering
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Detect Chrome binary location based on platform
        if sys.platform == "darwin":  # macOS
            if os.path.exists("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
                chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            else:
                print("Chrome not found in default location")
                return None
        
        # Initialize Chrome driver
        try:
            service = Service()
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("Successfully initialized Chrome driver")
        except Exception as e:
            print(f"Error creating Chrome driver with ChromeDriverManager: {e}")
            # Fallback to local ChromeDriver if available
            try:
                service = Service(executable_path="/usr/local/bin/chromedriver")
                driver = webdriver.Chrome(service=service, options=chrome_options)
                print("Successfully initialized Chrome driver with local ChromeDriver")
            except Exception as e2:
                print(f"Error creating Chrome driver with local ChromeDriver: {e2}")
                return None

        # Handle login
        try:
            driver.get("https://www.mountainproject.com")
            time.sleep(3)  # Wait for page to load
            
            if os.path.exists(COOKIE_FILE):
                # Try to load cookies
                try:
                    with open(COOKIE_FILE, "r") as f:
                        cookies = json.load(f)
                    for cookie in cookies:
                        driver.add_cookie(cookie)
                    print("Loaded cookies successfully")
                    
                    # Verify login worked by reloading page
                    driver.get("https://www.mountainproject.com")
                    time.sleep(3)
                    
                    # If we see login link, cookies didn't work
                    if driver.find_elements(By.CSS_SELECTOR, "a.login-link"):
                        print("Cookies expired, doing fresh login")
                        do_login()
                except Exception as e:
                    print(f"Error loading cookies: {e}")
                    do_login()
            else:
                print("No cookie file found, doing fresh login")
                do_login()
                
            return driver
                
        except Exception as e:
            print(f"Error during login process: {e}")
            if driver:
                driver.quit()
            return None
            
    except Exception as e:
        print(f"Error initializing driver: {e}")
        if driver:
            driver.quit()
        return None

def do_login():
    """Perform login with credentials"""
    global driver
    
    try:
        print("Starting login process...")
        driver.get("https://www.mountainproject.com")
        time.sleep(3)
        
        # Find and click login button to open modal
        login_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".login-link, .btn-login"))
        )
        print("Found login button, clicking...")
        login_button.click()
        time.sleep(2)
        
        # Wait for login form in modal
        print("Filling login form...")
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='email']"))
        )
        pass_input = driver.find_element(By.CSS_SELECTOR, "input[name='pass']")
        
        if not LOGIN_EMAIL or not LOGIN_PASSWORD:
            print("Error: Login credentials not found in environment variables")
            return False
        
        # Fill and submit form
        email_input.send_keys(LOGIN_EMAIL)
        pass_input.send_keys(LOGIN_PASSWORD)
        
        # Find and click submit button
        submit_button = driver.find_element(By.CSS_SELECTOR, "form[action='/auth/login/email'] button[type='submit']")
        print("Submitting login form...")
        submit_button.click()
        
        # Wait for login to complete
        time.sleep(5)
        
        # Verify login was successful by checking for user avatar
        try:
            user_menu = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".user-img-avatar"))
            )
            print("Login successful - found user menu")
            
            # Save cookies
            try:
                cookies = driver.get_cookies()
                if cookies:
                    with open(COOKIE_FILE, "w") as f:
                        json.dump(cookies, f)
                    print(f"Successfully saved {len(cookies)} cookies to {COOKIE_FILE}")
                    return True
                else:
                    print("No cookies found to save")
                    return False
            except Exception as e:
                print(f"Error saving cookies: {e}")
                return False
                
        except:
            print("Login failed - could not find user menu")
            return False
            
    except Exception as e:
        print(f"Error during login process: {e}")
        return False

def verify_cookie_file():
    """Verify cookie file exists and is valid"""
    if not os.path.exists(COOKIE_FILE):
        print(f"Cookie file {COOKIE_FILE} not found")
        return False
        
    try:
        with open(COOKIE_FILE, "r") as f:
            cookies = json.load(f)
        if not cookies:
            print("Cookie file is empty")
            return False
        print(f"Found {len(cookies)} cookies in {COOKIE_FILE}")
        return True
    except Exception as e:
        print(f"Error reading cookie file: {e}")
        return False

def get_comments(route_url):
    """Get all comments using the global driver with login"""
    global driver
    print(f"\nDEBUG: Getting comments for {route_url}")
    
    if not driver:
        print("DEBUG: No driver, initializing...")
        init_selenium_driver()
    
    try:
        driver.get(route_url)
        time.sleep(3)
        print("DEBUG: Page loaded")
        
        # Parse all comments
        soup = BeautifulSoup(driver.page_source, "html.parser")
        comments = []
        
        # Find the comments section by ID pattern
        comments_section = soup.find("div", id=lambda x: x and x.startswith("comments-Climb-Lib-Models-Route-"))
        if comments_section:
            # Get all comment tables
            comment_tables = comments_section.find_all("table", class_="main-comment")
            print(f"DEBUG: Found {len(comment_tables)} comments")
            
            for table in comment_tables:
                try:
                    # Get user info from bio div
                    bio_div = table.find("div", class_="bio")
                    comment_author = "N/A"
                    if bio_div:
                        user_link = bio_div.find("a")
                        if user_link:
                            comment_author = user_link.text.strip()
                    
                    # Get comment text from comment-body div
                    comment_body = table.find("div", class_="comment-body")
                    comment_text = "N/A"
                    if comment_body:
                        # Look for the full comment span
                        comment_span = comment_body.find("span", id=lambda x: x and x.endswith("-full"))
                        if comment_span:
                            comment_text = comment_span.text.strip()
                            print(f"DEBUG: Found comment: {comment_text[:50]}...")
                    
                    # Get comment time from permalink
                    time_span = table.find("span", class_="comment-time")
                    comment_time = "N/A"
                    if time_span:
                        time_link = time_span.find("a", class_="permalink")
                        if time_link:
                            comment_time = time_link.text.strip()
                    
                    comments.append({
                        "comment_author": comment_author,
                        "comment_text": comment_text,
                        "comment_time": comment_time
                    })
                except Exception as e:
                    print(f"DEBUG: Error parsing comment: {e}")
                    continue
            
            return comments
        else:
            print("DEBUG: No comments section found")
            return []
            
    except Exception as e:
        print(f"DEBUG: Error getting comments: {e}")
        return []

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
    # Find the div containing the sub-areas
    sub_areas_div = soup.find('div', class_='max-height max-height-md-0 max-height-xs-400')
    if sub_areas_div:
        # Find all area links in the left nav
        return [link for link in sub_areas_div.find_all('a', href=True)
                if '/area/' in link['href']]
    return []

def is_lowest_level_area(soup):
    # Check if this area has routes
    route_table = soup.find('table', {'id': 'left-nav-route-table'})
    if route_table and route_table.find_all('tr'):
        return True
    
    # Check sub-areas
    sub_areas_div = soup.find('div', class_='max-height max-height-md-0 max-height-xs-400')
    if sub_areas_div:
        sub_area_links = [link for link in sub_areas_div.find_all('a', href=True)
                         if '/area/' in link['href']]
        # If there are no sub-areas with routes, this is a lowest level area
        return len(sub_area_links) == 0
    
    return True

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
        
    print(f"Checking area: {url}")  # Debug print
    
    soup = get_soup(url)
    if soup is None:
        return lowest_level_urls
    
    current_area = get_current_area_name(soup)
    current_hierarchy = hierarchy + [current_area]
    
    # Get sub-area links
    sub_area_links = get_sub_area_links(soup)
    
    # If this area has routes, add it to lowest_level_urls
    route_table = soup.find('table', {'id': 'left-nav-route-table'})
    if route_table and route_table.find_all('tr'):
        print(f"Found routes in: {current_area}")  # Debug print
        lowest_level_urls.append(url)
    
    # Also check sub-areas
    for link in sub_area_links:
        if '/area/' in link['href']:
            sub_area_url = link['href'] if link['href'].startswith('http') else f"https://www.mountainproject.com{link['href']}"
            scrape_lowest_level_areas(sub_area_url, current_hierarchy, lowest_level_urls)
    
    return lowest_level_urls

# ==================== Route Details & Area Routes ====================

def get_route_details(route_url, retry_delay=30):
    """Add retry logic with exponential backoff for rate limits"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(route_url, headers={"User-Agent": "Mozilla/5.0"})
            if response.status_code == 429:  # Too Many Requests
                wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                print(f"Rate limited. Waiting {wait_time} seconds before retry...")
                sleep(wait_time)
                continue
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            route_details = {}
            
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
            route_details['route_comments'] = get_comments(route_url)
            
            # Fetch route stats: suggested ratings and tick comments.
            suggested_ratings, _, tick_comments = get_route_stats(route_url)
            route_details['route_suggested_ratings'] = suggested_ratings
            route_details['route_tick_comments'] = tick_comments
            
            return route_details
        except requests.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                print(f"Error: {e}. Retrying in {wait_time} seconds...")
                sleep(wait_time)
                continue
            raise
    # ... rest of the function ...

def get_route_stats(route_url):
    """Get route statistics using Selenium"""
    global driver
    try:
        stats_url = route_url.replace("/route/", "/route/stats/", 1)
        print(f"\nDEBUG: Fetching stats from {stats_url}")
        
        if not driver:
            init_selenium_driver()
            
        driver.get(stats_url)
        time.sleep(5)
        print("DEBUG: Initial page load complete")
        
        # Get suggested ratings from the table
        suggested_ratings = {}
        try:
            # Wait for the ratings table to load
            ratings_table = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h3:contains('Suggested Ratings') + table.table-striped"))
            )
            print("DEBUG: Found ratings table")
            
            # Get all rating rows
            rows = ratings_table.find_elements(By.TAG_NAME, "tr")
            print(f"DEBUG: Found {len(rows)} rating rows")
            
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 2:
                        # Get grade from the second cell
                        grade = cells[1].text.strip()
                        if grade and not grade.startswith('·'):  # Skip non-grade cells
                            print(f"DEBUG: Found rating: {grade}")
                            suggested_ratings[grade] = suggested_ratings.get(grade, 0) + 1
                except Exception as e:
                    print(f"DEBUG: Error parsing rating row: {e}")
                    continue
                    
        except Exception as e:
            print(f"DEBUG: Error getting ratings: {e}")
        
        # Get tick comments from the ticks table
        tick_comments = []
        try:
            # Find the ticks section
            ticks_div = driver.find_element(By.CSS_SELECTOR, "div.col-lg-6")
            rows = ticks_div.find_elements(By.CSS_SELECTOR, "tr")
            print(f"DEBUG: Found {len(rows)} tick rows")
            
            for row in rows:
                try:
                    # Find the comment div directly
                    comment_div = row.find_element(By.CSS_SELECTOR, "div.small div")
                    if comment_div:
                        text = comment_div.text.strip()
                        if text:
                            # Clean up the comment
                            text = re.sub(r'\b[A-Za-z]{3}\s+\d{1,2},\s*\d{4}\b', '', text)  # Remove date
                            text = re.sub(r'·.*?·', '', text)  # Remove climb type
                            text = re.sub(r'\s+', ' ', text).strip()
                            if text:
                                print(f"DEBUG: Found tick comment: {text[:50]}...")
                                tick_comments.append(text)
                except:
                    continue
                    
        except Exception as e:
            print(f"DEBUG: Error getting tick comments: {e}")
        
        print(f"DEBUG: Final results - {len(suggested_ratings)} ratings, {len(tick_comments)} comments")
        return suggested_ratings, None, " ".join(tick_comments)
        
    except Exception as e:
        print(f"DEBUG: Error in get_route_stats: {e}")
        return {}, None, ""

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
    
    area_comments = get_area_comments(area_url)
    
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
                
                # Add random delay between requests
                sleep(uniform(2, 4))  # Random delay between 2-4 seconds
                
                # Get the data-lr value
                data_lr = route_element.get('data-lr', 'N/A')
                
                route_details = get_route_details(route_url)
                ordered_route = {
                    "route_name": route_name, 
                    "route_url": route_url,
                    "route_lr": data_lr  # Add the data-lr value
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

def get_area_comments(area_url):
    """Get comments for an area using the existing driver"""
    global driver
    
    if not driver:
        init_selenium_driver()
    
    try:
        driver.get(area_url)
        time.sleep(3)
        
        # Scroll to bottom to trigger any lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
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
        
    except Exception as e:
        print(f"Error getting area comments: {e}")
        return []

if __name__ == "__main__":
    try:
        if len(sys.argv) < 2:
            print("Usage: python3 script.py 'base_url'")
            sys.exit(1)
            
        # Initialize driver and verify/create cookies
        driver = init_selenium_driver()
        if not driver:
            print("Failed to initialize Selenium driver")
            sys.exit(1)
            
        # Try login up to 3 times
        max_login_attempts = 3
        for attempt in range(max_login_attempts):
            if verify_cookie_file():
                print("Cookie file verified")
                break
                
            print(f"Login attempt {attempt + 1}/{max_login_attempts}...")
            if do_login():
                print("Login successful")
                break
            else:
                if attempt < max_login_attempts - 1:
                    print("Login failed, retrying...")
                    time.sleep(5)  # Wait before retry
                else:
                    print("All login attempts failed")
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
        
    finally:
        if driver:
            driver.quit()