UPDATE user_commodities AS uc
SET buy_price = v.buy_price
FROM (VALUES %s) AS v(buy_price, user_id, commodity_id)
WHERE uc.user_id = v.user_id AND uc.commodity_id = v.commodity_id;