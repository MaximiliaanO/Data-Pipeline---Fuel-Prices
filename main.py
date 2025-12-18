#! python3
#  Web-scraper to scrape price data from fuel stations from a specific Operator.

import logging, os
from scripts import scraper, db
from pathlib import Path

#Set directories (so it runs well on cron)
BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / 'logs' / 'main.log'
os.chdir(BASE_DIR)

#Logging config
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s', filename=str(LOG_FILE))

def main():
    logging.info("Starting scraper")

    #Step 1: Download HTML with nested JSON from main page.
    main_page = scraper.download_html()

    #Step 2: Parse JSON from main webpage.
    json_data = scraper.parse_html_stations(main_page)

    #Step 3: Initialize PostgreSQL connection:
    connection, cursor = db.create_connection()
    
    #Step 4: Initialize PostgreSQL tables (do nothing when already exists):
    db.create_db_tables(connection, cursor)

    #Step 5: Initialize/update transformed data to dimension table:
    db.update_station_data(connection, cursor, json_data)

    #Step 6: Retrieve individual station id's and links:
    links_dict = scraper.retrieve_ids_and_links(json_data)

    #Step 7: Retrieve latest event_id from PostgreSQL (primary key)
    event_id = db.latest_event_id(cursor)

    #Step 8: Retrieve transformed data on prices of individual stations
    price_list = scraper.retrieve_individual_prices(links_dict, event_id)

    #Step 9: Write transformed events data to fact table:
    db.update_fact_data(connection, cursor, price_list)

    #Step 10: Finalize updates and close connection:
    db.commit_finalized_connection_closed(connection, cursor)
    logging.info('Scraper finished.')

    print('Scraper finished, exiting program.')

if __name__ == '__main__':
    main()

