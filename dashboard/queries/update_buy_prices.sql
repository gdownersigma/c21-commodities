UPDATE user_commodities
SET buy_price = %s
WHERE user_id = %s AND commodity_id = %s;