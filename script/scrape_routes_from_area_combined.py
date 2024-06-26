import requests
from bs4 import BeautifulSoup
import re
import json
import sys

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

    route_details['description'] = description
    route_details['location'] = location
    route_details['protection'] = protection
    
    return route_details

def get_routes(area_url):
    response = requests.get(area_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    area_name = area_url.rstrip('/').split('/')[-1]
    gps_url = soup.find('a', href=re.compile(r'maps.google.com')).get('href')

    description_div = soup.find('div', {'class': 'fr-view'})
    description = description_div.text.strip() if description_div else 'N/A'
 
    getting_there_div = ''
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
        'routes': routes
    }
    
    return area_data

def save_area_info_to_json(area_info, filename):
    with open(filename, 'w') as f:
        json.dump(area_info, f, indent=4)
    print(f"Area info saved to {filename}")


# Example usage
area_url = 'https://www.mountainproject.com/area/114816092/upper-castle'
area_data = get_routes(area_url)
filename = f'{area_data["area_name"]}-routes.json'
save_area_info_to_json(area_data, filename)

