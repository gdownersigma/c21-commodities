SELECT commodity_id 
FROM user_commodities 
JOIN users 
    USING (user_id) 
WHERE user_id = %s;