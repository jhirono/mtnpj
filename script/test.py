import requests
from bs4 import BeautifulSoup

def scrape_route_details(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    route_details = {}

    # Scrape the FA
    fa_tag = soup.find(text='FA:')
    fa = fa_tag.find_next('td').text.strip() if fa_tag else 'N/A'
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
    
    return route_details

# Example usage
url = 'https://www.mountainproject.com/route/105842838/crime-of-the-century'
route_details = scrape_route_details(url)
print(route_details)
