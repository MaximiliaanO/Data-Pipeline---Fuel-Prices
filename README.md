
# ⛽ Data Pipeline: Fuel Price
Automated web scraper that collects fuel prices from a website, transforms the data and loads the data in a **PostgreSQL database** for further analysis.  
This project runs daily via a cronjob and keeps historical price data by writing each scrape event to a fact table.

## 📌 Features

- Scrapes **all gas stations** listed on the operator's website
- Extracts embedded JSON containing station metadata  
- Visits each station page individually to collect fuel prices  
- Automatically updates:
  - `dim_stations` (station metadata)
  - `fact_prices` (daily event-based fuel prices)
- Logs results to daily rotating log files  
- Fully configurable via `.env`  
- Ready for automated scheduling with cron  
- Modular Python structure:
  - `scraper.py` → web requests, HTML parsing, price extraction
  - `db.py` → PostgreSQL handling, inserts, updates
  - `main.py` → orchestrates full ETL pipeline

---

## 🗂 Project Structure


```
Fuel_Scraper
├─ env
|   └─ .env
├─ README.md
├─ scripts
│  ├─ db.py
│  ├─ scraper.py
│  ├─ sql
│  │  ├─ insertdim.sql
│  │  ├─ insertfact.sql
│  │  ├─ latest_event_id.sql
│  │  └─ tables.sql
│  └─ __init__.py
├─ tests
│  ├─ conftest.py
│  ├─ test_db.py
│  ├─ test_main.py
│  ├─ test_scraper.py
│  └─ __init__.py
├─ __init__.py
└─ main.py

```

---

## ⚙️ Installation

### 1. Clone repository

```bash
git clone https://github.com/<yourusername>/fuel-scraper.git
cd fuel-scraper
````

### 2. Install Python dependencies

Make sure you’re using Python 3.10+.

```bash
pip install -r requirements.txt
```

---

## 🔐 Environment Variables (.env)

Copy env/.env.example to env/.env and fill in your values:

```
env/.env
```

With:

```
DB_NAME=...
DB_USER=...
DB_PASS=...
DB_HOST=...

BASE_URL=https://example.com
USER_AGENT=FuelScraper/1.0
```

Environment variables are loaded inside:

* `scraper.py` (BASE_URL, USER_AGENT)
* `db.py` (database connection)

---

## 🏁 Running the Scraper

```bash
python main.py
```

The workflow performed:

1. Download main webpage (`download_html`)
2. Extract station list JSON (`parse_html_stations`)
3. Create DB tables if needed (`create_db_tables`)
4. Transform and Insert/Update station metadata (`update_station_data`)
5. Fetch latest event ID from Database (`latest_event_id`)
6. Scrape individual station prices (`retrieve_individual_prices`)
7. Transform and insert fact price data (`update_fact_data`)
8. Commit and close connection

---

## 📝 Logging

All scraper components write logs into the `logs/` directory.

Example configuration from code:

* `main.py` → `logs/main.log`
* `scraper.py` → `logs/scraper.log`
* `db.py` → `logs/db.log`

These logs record:

* HTTP activity  (INFO - Disabled by default)
* SQL operations (INFO - Disabled by default)
* Missing price data (WARNING)
* Errors and warnings (WARNING)

Daily log rotation can optionally be added using
`TimedRotatingFileHandler`.

---

## 🧩 Database Schema

### Dimension Table: `dim_stations`

Stores metadata for every station:

| Column        | Type  | Description          |
| ------------- | ----- | -------------------- |
| id            | int   | Station ID           |
| brand         | text  | Station brand        |
| guid          | text  | Link to detail page  |
| title         | text  | Name                 |
| street        | text  | Address              |
| postcode      | text  | Cleaned postcode     |
| city          | text  | City                 |
| category      | jsonb | Station category     |
| lat           | float | Latitude             |
| long          | float | Longitude            |
| open_time     | text  | Open / not open      |
| gasolineTypes | jsonb | Available fuel types |
| services      | jsonb | Additional services  |

### Fact Table: `fact_prices`

Stores event-based fuel prices:

| Column     | Type     |
| ---------- | -------- |
| event_id   | int - PK |
| station_id | int - FK |
| timestamp  | datetime |
| fuel_type  | text     |
| price      | float    |

The scraper inserts **one event per station** with available fuel prices.

---

## ⏱ Schedule Daily via Cron (Ubuntu)

Edit crontab:

```bash
crontab -e
```

Add:

```bash
0 8 * * * /usr/bin/python3 /home/username/fuel-scraper/main.py >> /home/username/fuel-scraper/logs/cron.log 2>&1
```

This runs once per day at 08:00.

---

## 🧪 Testing (Unit Tests)

Unit tests use:

* `pytest`
* `unittest.mock` for mocking:

  * HTTP requests
  * DB cursors
  * BeautifulSoup parsing

Example:

```bash
pytest -v
```

---

## 🚨 Error Handling

* SQL errors → rollback + continue
* HTML missing price → logged + skipped
* Missing fields in JSON → logged
* Connection errors → exception thrown

The scraper is highly fault-tolerant and continues processing stations even if a subset fails.

---

## 🔮 Potential Future Improvements

* Async scraping (1000+ station requests → few minutes)
* Progress bar for scraping
* Docker container for easy deployment
* Power BI dashboard template (visualisation)
* Notifications on price changes

---

## 📄 License

MIT License (of Choice)

---

## 👤 Author

Max — Python Developer & Data Professional
