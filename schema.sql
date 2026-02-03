DROP TABLE IF EXISTS market_records CASCADE;
DROP TABLE IF EXISTS user_commodities CASCADE;
DROP TABLE IF EXISTS commodities CASCADE;
DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE users (
    user_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    user_password VARCHAR(100) NOT NULL
);

CREATE TABLE commodities (
    commodity_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    commodity_name VARCHAR(100) NOT NULL,
    trade_month VARCHAR(10) NOT NULL,
    currency_code VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_commodities (
    user_commodity_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    commodity_id BIGINT REFERENCES commodities(commodity_id) ON DELETE CASCADE,
    buy_price FLOAT,
    sell_price FLOAT
);

CREATE TABLE market_records (
    market_record_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    commodity_id BIGINT REFERENCES commodities(commodity_id) ON DELETE CASCADE,
    current_at TIMESTAMP NOT NULL,
    price FLOAT NOT NULL,
    volume BIGINT,
    day_high FLOAT,
    day_low FLOAT,
    price_change FLOAT,
    change_percentage FLOAT,
    open_price FLOAT,
    previous_close FLOAT,
    price_avg_50 FLOAT,
    price_avg_200 FLOAT,
    year_high FLOAT,
    year_low FLOAT,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



