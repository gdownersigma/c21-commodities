SELECT recorded_at, price, change_percentage, day_high, day_low
FROM market_records
WHERE commodity_id = %s
AND recorded_at >= NOW() - INTERVAL '%s days'
ORDER BY recorded_at DESC
LIMIT 500;
