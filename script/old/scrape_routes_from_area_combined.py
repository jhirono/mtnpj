import requests
from bs4 import BeautifulSoup
import re
import json
import sys

def scrape_lowest_level_areas(url, hierarchy, lowest_level_urls):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Add current area to hierarchy
    current_area = soup.find('h1').text.strip()
    hierarchy.append(current_area)

    # Find sub-areas
    sub_areas_div = soup.find('div', class_='max-height max-height-md-0 max-height-xs-400')
    if not sub_areas_div:
        return []

    sub_area_links = sub_areas_div.find_all('a', href=True)
    sub_areas = [link for link in sub_area_links if '/area/' in link['href']]

    # If no sub-areas, it's a lowest level area
    if not sub_areas:
        lowest_level_urls.append(url)
        return

    # Recursively scrape each sub-area
    for sub_area in sub_areas:
        sub_area_url = sub_area['href']
        if not sub_area_url.startswith('http'):
            sub_area_url = 'https://www.mountainproject.com' + sub_area_url
        scrape_lowest_level_areas(sub_area_url, hierarchy[:], lowest_level_urls)  # Pass a copy of the hierarchy list to preserve state

