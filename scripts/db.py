# Handles DB communication

import psycopg2 as p
import re, logging, os, psycopg2.extras
from psycopg2.extras import Json
from dotenv import load_dotenv
from pathlib import Path
import asyncio
import asyncpg

BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR.parent / 'logs' / 'db.log'

#Load credentials from .env
load_dotenv(BASE_DIR.parent / 'env' /'.env')

#Logging config
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename=str(LOG_FILE))
logging.disable(logging.INFO)

class DbHandler():
    def __init__(self):
        self.async_conn = None
        self.sync_conn = None
        self.sync_cur = None
        self.coroutines = None

    def sync_connection(self) -> None:
        """Creates a connection and cursor to the database."""
        connection = p.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            host=os.getenv("DB_HOST")
            )
        if connection.status == 0:
            raise p.DatabaseError('Connection to the database has failed.')
        logging.debug('Connecion status: ' + str(connection.status) + ' (1 means connected)')
        psycopg2.extras.register_default_json(conn_or_curs=connection)
        psycopg2.extras.register_default_jsonb(conn_or_curs=connection)
        self.sync_conn = connection
        self.sync_cur = connection.cursor()

    def load_query(self, path: str | Path) -> str: 
        '''Opens needed .sql file and returns the query for psycopg2.'''
        with open(path, "r") as sql:
            return sql.read()
        
    def create_db_tables(self):
        """"Creates the tables in the database if it not yet exists."""
        query = self.load_query('scripts/sql/tables.sql') #Creates tables if not exists.
        logging.debug(query)
        try:
            self.sync_cur.execute(query)
            self.sync_conn.commit()
            logging.info("Create DB Tables: SQL executed and comitted")
            print('Database tables created.')
        except Exception as e:
            self.sync_conn.rollback()
            logging.error(f'Create DB Tables: Execution failed: {e}')
            print(f'Create DB Tables: Execution failed: {e}')

    def transform_postcode(self, id, postcode):
        '''Transforms dimension table postcodes'''
        match = re.search(r"^(\d{4})+(&nbsp;)?(\w\w{2})?(&nbsp;)?", postcode)
        try:
            if match.group(3) == None:
                return match.group(1)
            elif match.group(3):
                postcode = match.group(1) + match.group(3)
                return postcode
            else:
                logging.error(f'ETL: Error converting postcode: {str(postcode)} for station {str(id)}')
                return None
        except AttributeError as e:
            logging.error(f'ETL: AttributeError for {str(id)} and postcode: {str(postcode)}')
            logging.error(str(e))
            return None

    def update_station_data(self, json_data):
        """Inserts dimension data into the table dim_stations.
        Checks if all data is present and updates if necessary."""
        query = self.load_query('scripts/sql/insertdim.sql')
        logging.debug(query)
        
        #Retrieve data per station.
        error_count = 0
        for station in json_data['places']:
            if error_count == 5:
                break
            try:
                id = station['id'] #mandatory field
            except KeyError as e:
                logging.error('Update Station Data: KeyError whilst looping the gas station dim JSON: ' + str(e)) #Add to error count?
                continue
            brand = station.get('brand')
            guid = station.get('guid')
            title = station.get('title')
            street = station.get('street')
            postcode = self.transform_postcode(id, station.get('postcode'))
            city = station.get('city')
            category = station.get('category')
            if category == None:
                logging.warning(f'Update Station Data: Category not provided for station id: {id}')
            else:
                category = Json(category)
            lat = station.get('lat')
            lng = station.get('long')
            open_time = station.get('open')
            gasolinetypes = station.get('gasolineTypes') #Returns NONE when no data
            if gasolinetypes == None:
                logging.warning(f'Update Station Data: Gasoline types not provided for station id: {id}')
            else:
                gasolinetypes = Json(gasolinetypes)
            services = station.get('services') # Returns NONE when no data
            if services == None:
                logging.warning(f'Update Station Data: Services not provided for station-id: {id}')
            else:
                services = Json(services)
            
            # Tuple for values.
            values = (id, brand, guid, title, street, postcode, city, category, lat, lng, open_time, gasolinetypes, services)
            types = [type(x) for x in values]
            logging.debug(types)

            #Insert dimension attributes in PostgreSQL (test)
            try:
                self.sync_cur.execute(query, values)
                self.sync_conn.commit()
                logging.info("Insert dimension attributes in PostgreSQL: SQL executed and comitted")
            except Exception as e:
                self.sync_conn.rollback()
                logging.error(f'Insert dimension attributes in PostgreSQL: Execution failed: {e}')
                error_count += 1
                continue #Skip over this iteration go over though next
        print('Dimension station data updated.')

    def latest_event_id(self):
        '''Return latest event_id primary key from database.'''
        query = self.load_query('scripts/sql/latest_event_id.sql')
        logging.debug(query)
        self.sync_cur.execute(query)
        event_id = self.sync_cur.fetchone()[0]
        logging.debug(f'event id pre conditional: {str(event_id)}')
        if event_id == None:
            logging.debug(f'event ID when null: {str(event_id)}')
            event_id = 1
        else:
            event_id +=1
            logging.debug(f'Event ID when not null {str(event_id)}')
        print('Event ID fetched from Database.')
        return event_id
    
    def sync_close_conn(self):
        self.sync_conn.commit()
        self.sync_cur.close()
        self.sync_conn.close()
        print('Changed commited to database and closed connection.')
    
    async def async_connection(self):
        try:
            async_conn = await asyncpg.create_pool(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            min_size= 1,
            max_size= 10
            )
            self.async_conn = async_conn
        except Exception as e:
            #Mooi maken, sowieso logging nog aanpakken.
            print(f"An error has ocurred: {e}")
    
    async def update_fact_data(self, price_tup):
        query = self.load_query('scripts/sql/insertfact.sql')
        async with self.async_conn.acquire() as conn:
            await conn.execute(query, *price_tup)

    def generate_coroutines(self, pricelist):
        self.coroutines = [self.update_fact_data(price_tup=pt) for pt in pricelist]

    async def start(self, pricelist):
        await self.async_connection()
        self.generate_coroutines(pricelist=pricelist)
        await asyncio.gather(*self.coroutines)
        

    def run_db_handler(self, pricelist):
        asyncio.run(self.start(pricelist=pricelist))

