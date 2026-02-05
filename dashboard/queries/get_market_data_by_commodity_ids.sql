SELECT * FROM market_records
WHERE commodity_id IN %s
ORDER BY recorded_at DESC;