SELECT *
FROM market_records
JOIN commodities AS c
    USING (commodity_id)
WHERE commodity_id = %s;