SELECT DISTINCT ON (c.commodity_id)
    c.commodity_id,
    c.symbol,
    c.commodity_name,
    c.currency,
    m.price,
    m.change,
    m.change_percentage,
    m.day_high,
    m.day_low,
    m.volume,
    m.year_high,
    m.year_low,
    m.recorded_at
FROM commodities c
LEFT JOIN market_records m ON c.commodity_id = m.commodity_id
ORDER BY c.commodity_id, m.recorded_at DESC;
