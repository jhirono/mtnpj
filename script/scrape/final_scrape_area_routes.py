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
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Global Login Credentials & Cookie File ---
# Credentials are read from environment variables.
LOGIN_EMAIL = os.environ.get("MP_LOGIN_EMAIL")
LOGIN_PASSWORD = os.environ.get("MP_LOGIN_PASSWORD")
COOKIE_FILE = "cookies.json"

# ==================== Helper Functions ====================

def get_soup(url):
    """Get a BeautifulSoup object from a URL using requests."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return None

def get_current_area_name(soup):
    """Extract the area name from the soup (from the first <h1>)."""
    h1 = soup.find('h1')
    return h1.text.strip() if h1 else 'Unknown Area'

def get_sub_area_links(soup):
    """Extract sub-area links from the soup."""
    sub_areas_div = soup.find('div', class_='max-height max-height-md-0 max-height-xs-400')
    if not sub_areas_div:
        return []
    return sub_areas_div.find_all('a', href=True)

def is_lowest_level_area(sub_areas):
    """Determine if the current area is the lowest level (no further area links)."""
    return not any('/area/' in link['href'] for link in sub_areas)

def clean_area_name_from_url(url):
    """
    Derive a clean area name from the URL.
    For example, given:
      "https://www.mountainproject.com/area/110464982/lower-merced-river-canyon"
    It returns: "Lower Merced River Canyon"
    """
    last_segment = url.rstrip('/').split('/')[-1]
    return last_segment.replace('-', ' ').title()

def scrape_lowest_level_areas(url, hierarchy=None, lowest_level_urls=None):
    """
    Recursively find lowest-level area URLs.
    The function follows sub-area links until an area with no further area links is found.
    """
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

def get_comments(route_url, user_email=None, user_pass=None, cookie_file="cookies.json"):
    """
    Use Selenium to load the route page and scrape its visible comments.
    If a "load more comments" button exists, click it and log in if needed.
    Returns a list of comment dicts with keys:
    'comment_author', 'comment_text', and 'comment_time'.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Load homepage to set cookies if available.
    driver.get("https://www.mountainproject.com")
    if os.path.exists(cookie_file):
        try:
            with open(cookie_file, "r") as f:
                cookies = json.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
        except Exception as e:
            print("Error loading cookies:", e)
    
    driver.get(route_url)
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    
    load_more_elements = driver.find_elements(By.CSS_SELECTOR, "button.show-more-comments-trigger")
    if load_more_elements:
        print("Load more comments button found. Clicking it...")
        load_more = load_more_elements[0]
        load_more.click()
        time.sleep(2)
        login_form_elements = driver.find_elements(By.CSS_SELECTOR, "form[method='post'][action='/auth/login/email']")
        login_form = login_form_elements[0] if login_form_elements else None
        if login_form and user_email and user_pass:
            print("Login form detected. Logging in...")
            email_input = login_form.find_element(By.CSS_SELECTOR, "input[name='email']")
            pass_input = login_form.find_element(By.CSS_SELECTOR, "input[name='pass']")
            email_input.clear()
            email_input.send_keys(user_email)
            pass_input.clear()
            pass_input.send_keys(user_pass)
            login_button = login_form.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            WebDriverWait(driver, 20).until(
                EC.invisibility_of_element((By.CSS_SELECTOR, "form[method='post'][action='/auth/login/email']"))
            )
            print("Logged in successfully.")
            try:
                cookies = driver.get_cookies()
                with open(cookie_file, "w") as f:
                    json.dump(cookies, f)
            except Exception as e:
                print("Error saving cookies:", e)
    
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.comment-list"))
        )
    except Exception:
        driver.quit()
        return []
    
    page_source = driver.page_source
    driver.quit()
    
    soup = BeautifulSoup(page_source, "html.parser")
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

def get_area_comments(area_url, user_email=None, user_pass=None, cookie_file="cookies.json"):
    """
    Use Selenium to load the area page and scrape its visible comments.
    The logic is similar to get_comments() for routes.
    Returns a list of comment dicts with keys:
    'comment_author', 'comment_text', and 'comment_time'.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    # Load homepage for cookies.
    driver.get("https://www.mountainproject.com")
    if os.path.exists(cookie_file):
        try:
            with open(cookie_file, "r") as f:
                cookies = json.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
        except Exception as e:
            print("Error loading cookies:", e)
    
    driver.get(area_url)
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    
    load_more_elements = driver.find_elements(By.CSS_SELECTOR, "button.show-more-comments-trigger")
    if load_more_elements:
        print("Load more comments button found on area page. Clicking it...")
        load_more = load_more_elements[0]
        load_more.click()
        time.sleep(2)
        login_form_elements = driver.find_elements(By.CSS_SELECTOR, "form[method='post'][action='/auth/login/email']")
        login_form = login_form_elements[0] if login_form_elements else None
        if login_form and user_email and user_pass:
            print("Login form detected on area page. Logging in...")
            email_input = login_form.find_element(By.CSS_SELECTOR, "input[name='email']")
            pass_input = login_form.find_element(By.CSS_SELECTOR, "input[name='pass']")
            email_input.clear()
            email_input.send_keys(user_email)
            pass_input.clear()
            pass_input.send_keys(user_pass)
            login_button = login_form.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            WebDriverWait(driver, 20).until(
                EC.invisibility_of_element((By.CSS_SELECTOR, "form[method='post'][action='/auth/login/email']"))
            )
            print("Logged in successfully on area page.")
            try:
                cookies = driver.get_cookies()
                with open(cookie_file, "w") as f:
                    json.dump(cookies, f)
            except Exception as e:
                print("Error saving cookies:", e)
    
    time.sleep(3)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.comment-list"))
        )
    except Exception:
        driver.quit()
        return []
    
    page_source = driver.page_source
    driver.quit()
    
    soup = BeautifulSoup(page_source, "html.parser")
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

# ==================== Route Details & Area Routes ====================

def get_route_details(route_url):
    """
    Scrape static route details from the route page using requests.
    Also, use Selenium to scrape dynamic comments.
    Returns a dictionary with route details.
    """
    response = requests.get(route_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    route_details = {}
    
    # Route Grade
    grade_element = soup.select_one('.rateYDS, .route-type.Ice')
    if grade_element:
        grade_full = grade_element.text.strip()
        route_details['route_grade'] = grade_full.split()[0]
    else:
        route_details['route_grade'] = 'Unknown'
    
    # Route Stars and Votes
    stars_avg_tag = soup.find('span', id=re.compile(r'starsWithAvgText'))
    if stars_avg_tag:
        stars_avg_text = stars_avg_tag.text.strip()
        stars_match = re.search(r'Avg: (\d+(\.\d+)?)', stars_avg_text)
        votes_match = re.search(r'from (\d+)', stars_avg_text)
        route_details['route_stars'] = float(stars_match.group(1)) if stars_match else 'N/A'
        route_details['route_votes'] = int(votes_match.group(1)) if votes_match else 'N/A'
    else:
        route_details['route_stars'] = 'N/A'
        route_details['route_votes'] = 'N/A'
    
    # Route Type and Length
    type_length_tag = soup.find(string='Type:')
    if type_length_tag:
        type_length = type_length_tag.find_next('td').text.strip()
        type_length_split = type_length.split(',')
        types = []
        length = 'N/A'
        for item in type_length_split:
            item = item.strip()
            if 'ft' in item or 'm' in item:
                length = item
            else:
                types.append(item)
        route_details['route_type'] = ', '.join(types)
        route_details['route_length'] = length
    else:
        route_details['route_type'] = 'N/A'
        route_details['route_length'] = 'N/A'
    
    # Route FA (First Ascent)
    fa_tag = soup.find(string='FA:')
    if fa_tag:
        fa = fa_tag.find_next('td').text.strip()
        route_details['route_fa'] = fa
    else:
        route_details['route_fa'] = 'N/A'
    
    # Route Description, Location, and Protection
    route_description, route_location, route_protection = 'N/A', 'N/A', 'N/A'
    for h2_tag in soup.find_all('h2'):
        if "Description" in h2_tag.text:
            description_div = h2_tag.find_next('div', {'class': 'fr-view'})
            route_description = description_div.text.strip() if description_div else 'N/A'
        elif "Location" in h2_tag.text:
            location_div = h2_tag.find_next('div', {'class': 'fr-view'})
            route_location = location_div.text.strip() if location_div else 'N/A'
        elif "Protection" in h2_tag.text:
            protection_div = h2_tag.find_next('div', {'class': 'fr-view'})
            route_protection = protection_div.text.strip() if protection_div else 'N/A'
        elif "Gear" in h2_tag.text:
            gear_div = h2_tag.find_next('div', {'class': 'fr-view'})
            route_protection = gear_div.text.strip() if gear_div else 'N/A'
    
    route_details['route_description'] = route_description
    route_details['route_location'] = route_location
    route_details['route_protection'] = route_protection
    
    # Unique ID for the route
    route_details['route_id'] = str(uuid.uuid4())
    
    # Add empty tag arrays (to be populated later if needed)
    route_details['route_tags'] = []
    route_details['route_composite_tags'] = []
    
    # Scrape route comments using dynamic Selenium
    route_details['route_comments'] = get_comments(route_url, user_email=LOGIN_EMAIL, user_pass=LOGIN_PASSWORD, cookie_file=COOKIE_FILE)
    
    return route_details

def get_routes(area_url):
    """
    Scrape an area page for its routes and related data.
    Returns a dictionary representing the area with fields:
    area_id, area_url, area_name, area_gps, area_description, area_getting_there,
    area_tags, area_hierarchy, area_comments, and routes.
    """
    response = requests.get(area_url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Area basic fields
    area_name = area_url.rstrip('/').split('/')[-1]  # Fallback using URL segment
    description_div = soup.find('div', {'class': 'fr-view'})
    area_description = description_div.text.strip() if description_div else 'N/A'
    
    # Getting There
    area_getting_there = 'N/A'
    for h2_tag in soup.find_all('h2'):
        if "Getting There" in h2_tag.text:
            getting_there_div = h2_tag.find_next('div', {'class': 'fr-view'})
            area_getting_there = getting_there_div.text.strip() if getting_there_div else 'N/A'
            break

    # GPS (extract Google Maps link if available)
    area_gps = 'N/A'
    for tr in soup.find_all('tr'):
        if "GPS:" in tr.text:
            gps_tag = tr.find('a', {'target': '_blank', 'href': True})
            if gps_tag and 'maps.google.com' in gps_tag['href']:
                area_gps = gps_tag['href']
                break

    # Hierarchy (breadcrumb)
    area_hierarchy = []
    breadcrumb_div = soup.find('div', class_='mb-half small text-warm')
    if breadcrumb_div:
        links = breadcrumb_div.find_all('a')
        for idx, link in enumerate(links):
            raw_name = link.text.strip()
            if not raw_name or raw_name.endswith('…') or len(raw_name) < 5:
                cleaned_name = clean_area_name_from_url(link['href'])
            else:
                cleaned_name = raw_name
            area_hierarchy.append({
                "level": idx + 1,
                "area_hierarchy_name": cleaned_name,
                "area_hierarchy_url": link['href']
            })
    
    # Scrape area comments using dynamic Selenium
    area_comments = get_area_comments(area_url, user_email=LOGIN_EMAIL, user_pass=LOGIN_PASSWORD, cookie_file=COOKIE_FILE)
    
    # Scrape routes
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
                route_name = link_tag.text.strip()
                route_details = get_route_details(route_url)
                # Reorder keys so route_name and route_url come first.
                ordered_route = {
                    "route_name": route_name,
                    "route_url": route_url
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
        "area_comments": area_comments,
        "routes": routes
    }
    
    return area_data

# ==================== Retry Wrapper ====================

def safe_get_routes(url, retries=3, delay=5):
    """Attempt to get routes from an area URL with retries."""
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

# ==================== Save to JSON ====================

def save_urls_to_json(all_areas, base_url):
    """Save the scraped area and route data to a JSON file."""
    area_name = base_url.split('/')[-1]
    file_name = f"{area_name}_routes.json"
    try:
        with open(file_name, 'w') as f:
            json.dump(all_areas, f, indent=4)
            print(f"Data saved to {file_name}")
    except IOError as e:
        print(f"Error saving data to {file_name}: {e}")

# ==================== Main ====================

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