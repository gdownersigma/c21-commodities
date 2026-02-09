SELECT commodity_id 
FROM commodities 
WHERE LOWER(commodity_name) LIKE LOWER(%s)
OR LOWER(symbol) LIKE LOWER(%s)
LIMIT 1;
