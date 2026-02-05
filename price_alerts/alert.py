"""Script to check the RDS for alert conditions
 and send alerts based on previous Lambda"""
from os import environ as ENV
from dotenv import load_dotenv
from psycopg2 import connect
from generate_alert import generate_alert_email, get_logo_bytes
import boto3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage


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
        if action is not None:
            alerts.append(action)

    return alerts


def get_required_customer_info(action: tuple, latest_prices: dict) -> dict:
    """Get all the required customer info for sending alert"""
    alert_type, user_commodity = action

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.email, u.user_name, c.symbol, c.commodity_name
        FROM users u
        JOIN user_commodities uc ON u.user_id = uc.user_id
        JOIN commodities c ON uc.commodity_id = c.commodity_id
        WHERE u.user_id = %s AND c.commodity_id = %s
    """, (user_commodity['user_id'], user_commodity['commodity_id']))

    row = cur.fetchone()
    cur.close()
    conn.close()

    commodity_id = user_commodity['commodity_id']

    return {
        "alert_type": alert_type,
        "email": row[0],
        "user_name": row[1],
        "symbol": row[2],
        "commodity_name": row[3],
        "current_price": latest_prices[commodity_id]['price'],
        "target_price": user_commodity['buy_price'] if alert_type == 'buy' else user_commodity['sell_price'],
        "user_id": user_commodity['user_id'],  # Add this
        "commodity_id": commodity_id  # Add this
    }


def get_all_required_customer_info(actions: list[tuple], latest_prices: dict) -> list[dict]:
    """Get required customer info for all alerts"""
    return [get_required_customer_info(action, latest_prices) for action in actions]


def update_alerted_at(user_commodity: dict):
    """Update the alerted_at timestamp for the user commodity"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE user_commodities
        SET alerted_at = NOW()
        WHERE user_id = %s AND commodity_id = %s
    """, (user_commodity['user_id'], user_commodity['commodity_id']))
    conn.commit()
    cur.close()
    conn.close()


def get_generated_report_list(all_customer_info: list[dict]) -> list[str]:
    """Generate alert emails for all customer info and return as list of HTML strings"""
    return [generate_alert_email(info) for info in all_customer_info]


def send_emails(generated_reports: list[str], all_customer_info: list[dict]):
    """Send alert emails using AWS SES with embedded logo"""
    ses_client = boto3.client('ses', region_name='eu-west-2')
    sender_email = ENV.get("SENDER_EMAIL")
    logo_bytes = get_logo_bytes()

    for report, info in zip(generated_reports, all_customer_info):
        verified_emails = ses_client.list_verified_email_addresses()[
            'VerifiedEmailAddresses']
        if info['email'] not in verified_emails:
            print(f"Email {info['email']} is not verified in SES. Skipping.")
            continue

        # Create MIME message with embedded image
        msg = MIMEMultipart('related')
        msg['Subject'] = f"Price Alert for {info['commodity_name']}"
        msg['From'] = sender_email
        msg['To'] = info['email']

        # Attach HTML content
        html_part = MIMEText(report, 'html')
        msg.attach(html_part)

        # Attach logo image
        img = MIMEImage(logo_bytes)
        img.add_header('Content-ID', '<logo>')
        img.add_header('Content-Disposition', 'inline', filename='logo.png')
        msg.attach(img)

        response = ses_client.send_raw_email(
            Source=sender_email,
            Destinations=[info['email']],
            RawMessage={'Data': msg.as_string()}
        )
        print(f"Email sent to {info['email']}: {response['MessageId']}")
        update_alerted_at(info)


def handler(event, context):
    user_commodities = get_user_commodities()
    latest_prices = get_latest_prices(event)

    all_actions = check_all_alerts(user_commodities, latest_prices)
    all_customer_info = get_all_required_customer_info(
        all_actions, latest_prices)
    generated_reports = get_generated_report_list(all_customer_info)

    send_emails(generated_reports, all_customer_info)
    return {
        "statusCode": 200,
        "message": "Alerts processed successfully",
    }


if __name__ == "__main__":
    handler('fake event', None)
