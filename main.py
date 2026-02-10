#! python3
#  Web-scraper to scrape price data from fuel stations from a specific Operator.

import logging, os, time
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
    start = time.perf_counter()

    #Initialize classes
    dtb = db.DbHandler()
    dtb.sync_connection() #init connection (synchronous)
    dtb.create_db_tables() #init tables
    scrpr = scraper.Scraper(event_id=dtb.latest_event_id())

    #Run scraper
    scrpr.run(mode='fetch')
    finished_scraper = time.perf_counter()

    #Update dimension table (sync)
    dtb.update_station_data(json_data=scrpr.stations)
    dtb.sync_close_conn()

    #Update fact table (async)
    dtb.run_db_handler(pricelist=scrpr.pricelist)
    logging.info('Scraper finished.')
    end = time.perf_counter()

    print(f"""\nScraper ran in: {finished_scraper - start:.2f} seconds.
          \n Database ran in: {end - finished_scraper:.2f} seconds.
          \n Program ran in {end-start:.2f} seconds.""")

    print('Scraper finished, exiting program.')

if __name__ == '__main__':
    main()

