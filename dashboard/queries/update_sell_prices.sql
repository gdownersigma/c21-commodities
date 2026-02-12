UPDATE user_commodities AS uc
SET sell_price = v.sell_price
FROM (VALUES %s) AS v(sell_price, user_id, commodity_id)
WHERE uc.user_id = v.user_id AND uc.commodity_id = v.commodity_id;