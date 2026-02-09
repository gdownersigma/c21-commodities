SELECT DISTINCT ON (c.commodity_id)
    c.commodity_id,
    c.symbol,
    c.commodity_name,
    uc.buy_price as alert_buy_price,
    uc.sell_price as alert_sell_price,
    m.price as current_price,
    m.change_percentage,
    m.day_high,
    m.day_low
FROM user_commodities uc
JOIN commodities c ON uc.commodity_id = c.commodity_id
LEFT JOIN market_records m ON c.commodity_id = m.commodity_id
WHERE uc.user_id = %s
ORDER BY c.commodity_id, m.recorded_at DESC;
