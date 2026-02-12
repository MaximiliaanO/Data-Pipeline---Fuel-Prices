#! python3
#  Web-scraper to scrape price data from fuel stations from a specific Operator.

import logging, os, time, datetime, sys
from scripts import scraper, db
from pathlib import Path

#Set directories (so it runs well on cron)
BASE_DIR = Path(__file__).resolve().parent
logfile = str(datetime.datetime.now().date()) + '_scraper.log'
LOG_FILE = BASE_DIR / 'logs' / logfile
os.chdir(BASE_DIR)

#Logging config
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(module)s - %(levelname)s - %(message)s', 
    filename=str(LOG_FILE))

def main():
    logger.info("Starting scraper")
    start = time.perf_counter()

    #Initialize classes
    dtb = db.DbHandler()
    dtb.sync_connection() #init connection (synchronous)
    dtb.create_db_tables() #init tables
    scrpr = scraper.Scraper(event_id=dtb.latest_event_id())

    #Run scraper
    mode = scrpr.run(mode=None)
    finished_scraper = time.perf_counter()

    #Update dimension table (sync)
    dtb.update_station_data(json_data=scrpr.stations)
    dtb.sync_close_conn()

    #Update fact table (async)
    if mode == 'fetch':
        dtb.run_db_handler(pricelist=scrpr.pricelist)
    logger.info('Scraper finished.')
    end = time.perf_counter()

    logger.info(f"Scraper ran in: {finished_scraper - start:.2f} seconds.")
    logger.info(f"Database ran in: {end - finished_scraper:.2f} seconds.")
    logger.info(f"Program ran in {end-start:.2f} seconds.")

    print('Scraper finished, exiting program.')

if __name__ == '__main__':
    main()

