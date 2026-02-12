DELETE FROM user_commodities
WHERE (user_id, commodity_id) IN %s;