-- Initialize the fact table.
CREATE TABLE IF NOT EXISTS public.fact_prices
(
    event_id INT PRIMARY KEY,
    id INT,
    date_time TIMESTAMP,
    fuel_type TEXT,
    price REAL
);
-- Initialize the dim table.
CREATE TABLE IF NOT EXISTS public.dim_stations
(
    id INT PRIMARY KEY,
    brand TEXT,
    guid TEXT,
    title TEXT,
    street TEXT,
    postcode TEXT,
    city TEXT,
    category JSONB,
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,
    open_now TEXT,
    gasolinetypes JSONB,
    services JSONB
);