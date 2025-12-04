-- Insert Station Attributes in Dimension Table.
INSERT INTO dim_stations (
    id,
    brand,
    guid,
    title,
    street,
    postcode,
    city,
    category,
    lat,
    lng,
    open_now,
    gasolinetypes,
    services
)
VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) -- Values filled by python variables
-- On conflict only update if something has changed.
ON CONFLICT (id) DO UPDATE SET
    brand = EXCLUDED.brand,
    guid = EXCLUDED.guid,
    title = EXCLUDED.title,
    street = EXCLUDED.street,
    postcode = EXCLUDED.postcode,
    city = EXCLUDED.city,
    category = EXCLUDED.category,
    lat = EXCLUDED.lat,
    lng = EXCLUDED.lng,
    open_now = EXCLUDED.open_now,
    gasolinetypes = EXCLUDED.gasolinetypes,
    services = EXCLUDED.services
WHERE
    dim_stations.brand IS DISTINCT FROM EXCLUDED.brand OR
    dim_stations.guid IS DISTINCT FROM EXCLUDED.guid OR
    dim_stations.title IS DISTINCT FROM EXCLUDED.title OR
    dim_stations.street IS DISTINCT FROM EXCLUDED.street OR
    dim_stations.postcode IS DISTINCT FROM EXCLUDED.postcode OR
    dim_stations.city IS DISTINCT FROM EXCLUDED.city OR
    dim_stations.category IS DISTINCT FROM EXCLUDED.category OR
    dim_stations.lat IS DISTINCT FROM EXCLUDED.lat OR
    dim_stations.lng IS DISTINCT FROM EXCLUDED.lng OR
    dim_stations.open_now IS DISTINCT FROM EXCLUDED.open_now OR
    dim_stations.gasolinetypes IS DISTINCT FROM EXCLUDED.gasolinetypes OR
    dim_stations.services IS DISTINCT FROM EXCLUDED.services;