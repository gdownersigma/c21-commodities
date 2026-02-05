DELETE FROM user_commodities
WHERE user_id = %s
  AND commodity_id = %s;