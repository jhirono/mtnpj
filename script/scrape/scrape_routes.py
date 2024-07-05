import requests
from bs4 import BeautifulSoup
import json
import sys
import re
import uuid

def get_soup(url):
    """Get BeautifulSoup object from URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises HTTPError for bad responses
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        print(f"Request error: {e}")
        return None

def get_current_area_name(soup):
    """Extract the current area name from the soup."""
    return soup.find('h1').text.strip()

def get_sub_area_links(soup):
    """Extract sub-area links from the soup."""
    sub_areas_div = soup.find('div', class_='max-height max-height-md-0 max-height-xs-400')
    if not sub_areas_div:
        return []
    return sub_areas_div.find_all('a', href=True)

def is_lowest_level_area(sub_areas):
    """Check if the current area is the lowest level by sub-areas presence."""
    return not any('/area/' in link['href'] for link in sub_areas)

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
                sub_area_url = BASE_URL + link['href'] if not link['href'].startswith('http') else link['href']
                scrape_lowest_level_areas(sub_area_url, hierarchy[:], lowest_level_urls)  # Pass a copy of the hierarchy list

    return lowest_level_urls

def get_route_details(route_url):
    response = requests.get(route_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Initialize a dictionary to store route details
    route_details = {}

    # Scrape the grade
    grade_element = soup.select_one('.rateYDS, .route-type.Ice')
    if grade_element:
        grade_full = grade_element.text.strip()
        grade = grade_full.split()[0]  # Get only the grade value before the space
        route_details['grade'] = grade
    else:
        route_details['grade'] = 'Unknown'

    # Scrape the number of stars and votes
    stars_avg_text = soup.find('span', id=re.compile(r'starsWithAvgText')).text.strip()
    stars_match = re.search(r'Avg: (\d+(\.\d+)?)', stars_avg_text)
    votes_match = re.search(r'from (\d+)', stars_avg_text)
    stars = stars_match.group(1) if stars_match else 'N/A'
    votes = votes_match.group(1) if votes_match else 'N/A'
    route_details['stars'] = float(stars) if stars != 'N/A' else 'N/A'
    route_details['votes'] = int(votes) if votes != 'N/A' else 'N/A'
    
    # Scrape the type and length
    type_length = soup.find(text='Type:').find_next('td').text.strip()
    type_length_split = type_length.split(',')

    # Initialize an empty list to store the types
    types = []

    # Initialize length as 'N/A' by default
    length = 'N/A'

    # Loop through the split values to separate types and length
    for item in type_length_split:
        item = item.strip()
        if 'ft' in item or 'm' in item:  # Check if the item contains length information
            length = item
        else:
            types.append(item)

    # Join the types into a single string separated by commas
    route_details['type'] = ', '.join(types)
    route_details['length'] = length
    
    # Scrape the FA
    fa = soup.find(text='FA:').find_next('td').text.strip()
    route_details['fa'] = fa
    
    # Scrape the description, location, and protection
    description, location, protection = 'N/A', 'N/A', 'N/A'
    for h2_tag in soup.find_all('h2'):
        if "Description" in h2_tag.text:
            description_div = h2_tag.find_next('div', {'class': 'fr-view'})
            description = description_div.text.strip() if description_div else 'N/A'
        elif "Location" in h2_tag.text:
            location_div = h2_tag.find_next('div', {'class': 'fr-view'})
            location = location_div.text.strip() if location_div else 'N/A'
        elif "Protection" in h2_tag.text:
            protection_div = h2_tag.find_next('div', {'class': 'fr-view'})
            protection = protection_div.text.strip() if protection_div else 'N/A'
        elif "Gear" in h2_tag.text:
            gear_div = h2_tag.find_next('div', {'class': 'fr-view'})
            protection = gear_div.text.strip() if gear_div else 'N/A'

    route_details['description'] = description
    route_details['location'] = location
    route_details['protection'] = protection

    # Add a unique ID to the route
    route_details['route_unique_id'] = str(uuid.uuid4())
    
    return route_details

def get_routes(area_url):
    response = requests.get(area_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    area_name = area_url.rstrip('/').split('/')[-1]
    gps_url = soup.find('a', href=re.compile(r'maps.google.com')).get('href')

    description_div = soup.find('div', {'class': 'fr-view'})
    description = description_div.text.strip() if description_div else 'N/A'
 
    getting_there= ''
    for h2_tag in soup.find_all('h2'):
        if "Getting There" in h2_tag.text:
            getting_there_div = h2_tag.find_next('div', {'class': 'fr-view'})
            getting_there = getting_there_div.text.strip() if getting_there_div else 'N/A'
            break

    gps_url = 'N/A'
    for tr in soup.find_all('tr'):
        if "GPS:" in tr.text:
            gps_tag = tr.find('a', {'target': '_blank', 'href': True})
            gps_url = gps_tag['href'] if gps_tag and 'maps.google.com' in gps_tag['href'] else 'N/A'
            break

    # Scrape hierarchy
    hierarchy = []
    breadcrumb_div = soup.find('div', class_='mb-half small text-warm')
    if breadcrumb_div:
        links = breadcrumb_div.find_all('a')
        for link in links:
            hierarchy.append({
                'name': link.text.strip(),
                'url': link['href']
            })

    routes = []
    # Locate route table by more specific means
    route_table = soup.find('table', {'id': 'left-nav-route-table'})
    if route_table:
        route_elements = route_table.find_all('tr')
        for route_element in route_elements:
            link_tag = route_element.find('a')
            if link_tag:
                route_url = link_tag['href']
                route_name = link_tag.text.strip()
        
                # Get additional route details
                route_details = get_route_details(route_url)
                route_details['route_name'] = route_name
                route_details['route_url'] = route_url
        
                routes.append(route_details)
    
    area_data = {
        'url': area_url,
        'area_name': area_name,
        'gps': gps_url,
        'description': description,
        'getting_there': getting_there,
        'hierarchy': hierarchy,
        'routes': routes
    }
    
    return area_data

def save_urls_to_json(base_url):
    area_name = base_url.split('/')[-1]  # Extract the area name from the base_url
    file_name = f"{area_name}_routes.json"  # Create the file name
    try:
        with open(file_name, 'w') as f:
            json.dump(all_areas, f, indent=4)
            print(f"URLs saved to {file_name}")
    except IOError as e:
        print(f"Error saving URLs to {file_name}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scrape_area.py 'base_url'")
        sys.exit(1)  # Exit the script if no base URL is provided

    BASE_URL = sys.argv[1]  # Use the provided base URL
    lowest_level_urls = scrape_lowest_level_areas(BASE_URL)
    all_areas = []
    for index, url in enumerate(lowest_level_urls, start=1):
        try:
            print(f"Scraping {url} ({index}/{len(lowest_level_urls)})...")
            area_details = get_routes(url)
            all_areas.append(area_details)
        except Exception as e:
            print(f"Error processing {url}: {e}")

    save_urls_to_json(BASE_URL)