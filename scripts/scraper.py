# This module handles all the web requests, html and json parsing.

import logging, bs4, re, json, time, os, aiohttp, asyncio
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
import time

#Set logging directory
BASE_DIR = Path(__file__).resolve().parent

#Logging
logger = logging.getLogger(__name__)

#Load credentials from .env
load_dotenv(BASE_DIR.parent / 'env' /'.env')

class Scraper():
    def __init__(self, base_url:str=os.getenv('BASE_URL'), event_id:int=0):
        self.base_url = base_url
        self.sem = asyncio.Semaphore(15)
        self.session = None
        self.base_page = None
        self.stations = None
        self.links = None
        self.coroutines = None
        self.cororesponses = []
        self.pricelist = None
        self.event_id = event_id

    async def init_session(self):
        """"Initialize the client session."""
        session = aiohttp.ClientSession()
        self.session = session

    async def get_base_page(self):
        """Return main page of the scraper"""
        headers = {"user-agent" : os.getenv('USER_AGENT')}
        try:
            async with self.session.get(url=self.base_url, headers=headers) as resp:
                page = await resp.text()
                self.base_page = page
        except Exception as e:
            logger.error('An error has ocurred: %s', e)

    def parse_base(self):
        '''Parses html, extracts the json list of gas stations as json-str'''
        soup = bs4.BeautifulSoup(self.base_page, 'html.parser')
        scripts = soup.find_all('script') # find all items with the <script> tag.
        logger.debug(type(scripts))

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
        logger.debug(type(json_text)) #Check if correctly returns a dict.
        self.stations = json_text

    def get_links(self):
        '''From the all stations JSON extract the station id's and the links to the gas station specific pages.
        This is needed to get the gas station specific prices.'''
        logger.debug('Check length of json: ' + str(len(self.stations['places'])))
        links_dict = {self.stations['places'][i]['id']:self.stations['places'][i]['guid'] for i in range(len(self.stations['places']))} #key: self.stations['places'][i]['id'] value: json_text['places'][i]['guid']
        print('Station links dict created.')
        self.links = links_dict # key, value = {id : link}

    async def fetch_station(self, station_id, url):
        async with self.sem:
            async with self.session.get(url=url) as resp:
                html = await resp.text()
                self.cororesponses.append({station_id: html})
    
    def generate_coroutines(self):
        self.coroutines = [self.fetch_station(station_id=id, url=link) for id, link in self.links.items()]

    def parse_prices(self):
        '''Returns a list of tuples with (id, timestamp, fueltype, price) this will be inserted in the fact table.'''
        pricelist = [] # Initialize lists with all prices for all gas stations. List wil contain tuples (id(str), fueltype(str), price(float))
        no_price = 0
        for station in self.cororesponses:
            for id, html in station.items():
                soup = bs4.BeautifulSoup(html, 'html.parser')
                price_elems = soup.select('.price')
                if len(price_elems) == 0:
                    no_price += 1
                    continue
                prijzen = [float(price.getText()[2:]) for price in price_elems] #List with prices #1: Benzine #2: Diesel #3:LPT (optional)
                prijzen.reverse()
                logger.debug(prijzen)
                logger.debug('Hoevelheid prijzen: ' + str(len(prijzen)))
                if len(price_elems) == 2:
                    for i in range(len(prijzen)):
                        if i == 0:
                            pricelist.append((self.event_id, id, datetime.now(), 'benzine', prijzen[(i - 1)]))
                            logger.debug(f'Benzine: {prijzen[(i - 1)]}')
                        elif i == 1:
                            pricelist.append((self.event_id, id, datetime.now(), 'diesel', prijzen[(i - 1)]))
                            logger.debug(f'Diesel: {prijzen[(i - 1)]}')
                    self.event_id += 1
                elif len(price_elems) == 3:
                        for i in range(len(prijzen)):
                            if i == 0:
                                pricelist.append((self.event_id, id, datetime.now(), 'benzine', prijzen[(i - 1)]))
                                logger.debug(f'Benzine: {prijzen[(i - 1)]}')
                            elif i == 1:
                                pricelist.append((self.event_id, id, datetime.now(), 'lpg', prijzen[(i - 1)]))
                                logger.debug(f'LPG: {prijzen[(i - 1)]}')
                            elif i == 2:
                                pricelist.append((self.event_id, id, datetime.now(), 'diesel', prijzen[(i - 1)]))
                                logger.debug(f'Diesel: {prijzen[(i - 1)]}')
                            self.event_id += 1
        logger.warning(f'Stations without price: {str(no_price)}')
        print('Pricelist per station created.')
        self.pricelist = pricelist # Returns a list of tuples per entry with (event_id, id, timestamp, fueltype, price)

    async def close_session(self):
        """Close the session."""
        if self.session:
            await self.session.close()

    async def run_scraper(self, mode:str=None):
        """If no argument passed to mode: only fetches the base data (links, stations).
           If 'fetch' passed to mode fetches base and price data."""
        start = time.perf_counter()
        await self.init_session()
        try:
            await self.get_base_page()
            self.parse_base() #Stations JSON-str: self.stations
            self.get_links() #Links dict {id : link} self.links
            end_base = time.perf_counter()
            if mode =='fetch':
                self.generate_coroutines()
                await self.init_session()
                await asyncio.gather(*self.coroutines)
                self.parse_prices()
        finally:
            await self.close_session()
        end = time.perf_counter()
        logger.info(f"Extracted base page in: {end_base - start:.2f} seconds.")
        logger.info(f"Fetched all pages: {end - end_base:.2f} seconds.")
        logger.info(f"Ran scraper in {end - start:.2f} seconds.")
    
    def run(self, mode:str=None):
        """If no argument passed to mode: only fetches the base data (links, stations).
           If 'fetch' passed to mode fetches base and price data."""
        asyncio.run(self.run_scraper(mode=mode))
        return mode
