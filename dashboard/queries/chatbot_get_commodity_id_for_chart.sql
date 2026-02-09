SELECT commodity_id 
FROM commodities 
WHERE commodity_name ILIKE %s OR symbol ILIKE %s;
