"""Script to check the RDS for alert conditions
 and send alerts based on previous Lambda"""
from os import environ as ENV
from dotenv import load_dotenv
from psycopg2 import connect

test_global_event = {
    "statusCode": 200,
    "body": [
        {
            "commodity_id": 10,
            "price": 67.39
        },
        {
            "commodity_id": 21,
            "price": 303.75
        },
        {
            "commodity_id": 24,
            "price": 6951.75
        },
        {
            "commodity_id": 27,
            "price": 2261.1
        },
        {
            "commodity_id": 40,
            "price": 89.27
        },
        {
            "commodity_id": 8,
            "price": 6.038
        },
        {
            "commodity_id": 17,
            "price": 3.359
        },
        {
            "commodity_id": 18,
            "price": 5048.3
        },
        {
            "commodity_id": 12,
            "price": 63.35
        },
        {
            "commodity_id": 22,
            "price": 25459.25
        }
    ]
}


def get_conn():
    """Establishes and returns a connection to the PostgreSQL database."""
    conn = connect(
        dbname=ENV.get("DB_NAME"),
        user=ENV.get("DB_USER"),
        password=ENV.get("DB_PASSWORD"),
        host=ENV.get("DB_HOST"),
        port=ENV.get("DB_PORT"),
    )
    return conn


def get_user_commodities() -> list[dict]:
    """Fetch all user commodities data and return as a list of dictionaries"""
    conn = get_conn()
    query = """
        SELECT * FROM user_commodities 
        WHERE (buy_price IS NOT NULL OR sell_price IS NOT NULL)
        AND (alerted_at IS NULL OR alerted_at < NOW() - INTERVAL '2 hours');"""
    cur = conn.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    result = [dict(zip(columns, row)) for row in rows]
    cur.close()
    conn.close()
    return result


def get_latest_prices(event: dict) -> dict:
    """Fetch latest prices for all commodities"""
    prices_list = event["body"]
    return {
        commodity_price['commodity_id']: commodity_price for commodity_price in prices_list}


def check_one_alert(user_commodity: dict, commodity_price: dict) -> tuple:
    """Check if an alert condition is met for the user commodity"""
    if commodity_price is None:
        return None

    buy_price = user_commodity.get("buy_price")
    sell_price = user_commodity.get("sell_price")

    if buy_price is not None and commodity_price['price'] <= buy_price:
        return ('buy', user_commodity)
    if sell_price is not None and commodity_price['price'] >= sell_price:
        return ('sell', user_commodity)
    return None


def check_all_alerts(user_commodities: list[dict], latest_prices: dict) -> list[tuple]:
    """Check all user commodities against latest prices for alerts"""
    alerts = []

    for user_commodity in user_commodities:
        action = check_one_alert(user_commodity, latest_prices.get(
            user_commodity['commodity_id']))
        alerts.append(action)

    return [alert for alert in alerts if alert is not None]


def get_required_customer_info(action: tuple, latest_prices: dict) -> dict:
    """Get all the required customer info for sending alert"""
    alert_type, user_commodity = action

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.email, u.user_name
        FROM users u
        WHERE u.user_id = %s
    """, (user_commodity['user_id'],))

    row = cur.fetchone()
    cur.close()
    conn.close()

    commodity_id = user_commodity['commodity_id']

    return {
        "alert_type": alert_type,
        "email": row[0],
        "user_name": row[1],
        "current_price": latest_prices[commodity_id]['price'],
        "target_price": user_commodity['buy_price'] if alert_type == 'buy' else user_commodity['sell_price']
    }


def get_all_required_customer_info(actions: list[tuple], latest_prices: dict) -> list[dict]:
    """Get required customer info for all alerts"""
    return [get_required_customer_info(action, latest_prices) for action in actions]


if __name__ == "__main__":
    load_dotenv()
    user_commodities = get_user_commodities()
    # print(user_commodities[0])  # Placeholder for actual alert logic
    latest_prices = get_latest_prices(test_global_event)

    all_actions = check_all_alerts(user_commodities, latest_prices)
    all_customer_info = get_all_required_customer_info(
        all_actions, latest_prices)
    print(all_customer_info[0])  # Placeholder for actual alert logic
