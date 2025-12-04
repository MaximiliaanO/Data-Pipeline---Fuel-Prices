-- Insert prices into fact table.
INSERT INTO fact_prices(
    event_id,
    id,
    date_time,
    fuel_type,
    price
)
VALUES(%s, %s, %s, %s, %s)
ON CONFLICT (event_id) DO NOTHING;