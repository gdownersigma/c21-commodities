SELECT * FROM user_commodities
WHERE (buy_price IS NOT NULL OR sell_price IS NOT NULL)
AND (alerted_at IS NULL OR alerted_at < NOW() - INTERVAL '2 hours');