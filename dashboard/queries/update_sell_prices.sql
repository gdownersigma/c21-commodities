UPDATE user_commodities
SET sell_price = %s
WHERE user_id = %s AND commodity_id = %s;