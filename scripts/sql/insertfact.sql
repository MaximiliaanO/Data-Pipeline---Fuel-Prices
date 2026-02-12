-- Insert prices into fact table.
INSERT INTO fact_prices(
    event_id,
    id,
    date_time,
    fuel_type,
    price
)
VALUES($1, $2, $3, $4, $5)
ON CONFLICT (event_id) DO NOTHING;