SELECT u.email, u.user_name, c.symbol, c.commodity_name
FROM users u
JOIN user_commodities uc ON u.user_id = uc.user_id
JOIN commodities c ON uc.commodity_id = c.commodity_id
WHERE u.user_id = %s AND c.commodity_id = %s;