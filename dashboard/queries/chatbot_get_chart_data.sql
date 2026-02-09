SELECT 
    m.recorded_at,
    m.price,
    m.change_percentage,
    m.day_high,
    m.day_low,
    c.commodity_name,
    c.symbol
FROM market_records m
JOIN commodities c ON m.commodity_id = c.commodity_id
WHERE m.commodity_id IN %s
AND m.recorded_at >= NOW() - INTERVAL '%s days'
ORDER BY m.recorded_at ASC;
