UPDATE user_commodities
SET alerted_at = NOW()
WHERE user_id = %s AND commodity_id = %s;
