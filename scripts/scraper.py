# This module handles all the web requests, html and json parsing.

#Import modules:
import logging, requests, bs4, re, json, time, os
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

#Set logging directory
BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR.parent / 'logs' / 'scraper.log'

#Load credentials from .env
load_dotenv(BASE_DIR.parent / 'env' /'.env')
BASE_URL=os.getenv('BASE_URL')
USER_AGENT = os.getenv('USER_AGENT')

#Logging configuration.
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename=str(LOG_FILE))
logging.disable(logging.INFO)

#Scraper functions
def download_html(url=BASE_URL): # Hoofdpagina met JSON van alle tankstations.
    '''Requests and downloads the selected URL'''
    try:
        headers = {'user-agent' : USER_AGENT}
        logging.info('url: %s' %url)
        request_response = requests.get(url, headers=headers)
        request_response.raise_for_status()
        return request_response
    except requests.exceptions.HTTPError as e:
        logging.error('HTTP error ocurred:', e)

def parse_html_stations(request_response):
    '''Parses the html of the request returned (std url) and extracts the json list of gas stations'''
    html = request_response.text
    soup = bs4.BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script') # find all items with the <script> tag.
    logging.debug(type(scripts))

    #Find the JSON with all the gas stations.
    for script in scripts:
        if 'placesInitialData' in script.text:
            json_data = script.text

    #Regex to find the substring in <script> with the json {substring}
    json_regex = re.search(
        r'var\s+placesInitialData\s*=\s*(\{.*?\});',
        json_data,
        re.DOTALL
    )

    #Raise error if JSON not found.
    if not json_regex:
        raise ValueError('Could find JSON in script-tag!')

    #Create dict form JSON formatted string.
    json_text = json.loads(json_regex.group(1))
    logging.debug(type(json_text)) #Check if correctly returns a dict.
    return json_text

def retrieve_ids_and_links(json_text):
    '''From the all stations JSON extract the station id's and the links to the gas station specific pages.
    This is needed to get the gas station specific prices.'''
    logging.debug('Check length of json: ' + str(len(json_text['places'])))
    links_dict = {json_text['places'][i]['id']:json_text['places'][i]['guid'] for i in range(len(json_text['places']))} #key: json_text['places'][i]['id'] value: json_text['places'][i]['guid']
    print('Station links dict created.')
    return links_dict # key, value = {id : link}

def retrieve_individual_prices(links_dict, event_id):
    '''Returns a list of tuples with (id, timestamp, fueltype, price) this will be inserted in the fact table.'''
    pricelist = [] # Initialize lists with all prices for all gas stations. List wil contain tuples (id(str), fueltype(str), price(float))
    no_price = 0
    for id, link in links_dict.items():
        logging.debug('Url: ' + link)
        response = download_html(url=link)
        soup = bs4.BeautifulSoup(response.text, 'html.parser')
        price_elems = soup.select('.price')
        if len(price_elems) == 0:
            no_price += 1
            continue
        prijzen = [float(price.getText()[2:]) for price in price_elems] #List with prices #1: Benzine #2: Diesel #3:LPT (optional)
        prijzen.reverse()
        logging.debug(prijzen)
        logging.debug('Hoevelheid prijzen: ' + str(len(prijzen)))
        if len(price_elems) == 2:
            for i in range(len(prijzen)):
                if i == 0:
                    pricelist.append((event_id, id, datetime.now(), 'benzine', prijzen[(i - 1)]))
                    logging.debug(f'Benzine: {prijzen[(i - 1)]}')
                elif i == 1:
                    pricelist.append((event_id, id, datetime.now(), 'diesel', prijzen[(i - 1)]))
                    logging.debug(f'Diesel: {prijzen[(i - 1)]}')
            event_id += 1
        elif len(price_elems) == 3:
                for i in range(len(prijzen)):
                    if i == 0:
                        pricelist.append((event_id, id, datetime.now(), 'benzine', prijzen[(i - 1)]))
                        logging.debug(f'Benzine: {prijzen[(i - 1)]}')
                    elif i == 1:
                        pricelist.append((event_id, id, datetime.now(), 'lpg', prijzen[(i - 1)]))
                        logging.debug(f'LPG: {prijzen[(i - 1)]}')
                    elif i == 2:
                        pricelist.append((event_id, id, datetime.now(), 'diesel', prijzen[(i - 1)]))
                        logging.debug(f'Diesel: {prijzen[(i - 1)]}')
                    event_id += 1
        # 0.1 second sleep for server load courtesy.
        time.sleep(0.1)
    logging.warning(f'Stations without price: {str(no_price)}')
    print('Pricelist per station created.')
    return pricelist # Returns a list of tuples per entry with (id, timestamp, fueltype, price)