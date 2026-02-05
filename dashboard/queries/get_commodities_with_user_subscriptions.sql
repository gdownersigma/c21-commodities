SELECT
	uc.user_id,
    c.commodity_id,
    c.commodity_name,
    COALESCE(uc.buy_price, 0) as buy_price,
    COALESCE(uc.sell_price, 0) as sell_price
FROM commodities c
LEFT JOIN user_commodities uc
    ON c.commodity_id = uc.commodity_id
    AND uc.user_id = %s;