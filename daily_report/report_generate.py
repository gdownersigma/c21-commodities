"""Script to generate HTML reports for each user from extracted data."""
import os
from io import BytesIO
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import boto3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from report_extract import (
    get_previous_day_date,
    extract_user_commodities,
    extract_market_records,
)


def get_logo_bytes() -> bytes:
    """Load logo and return as bytes."""
    logo_path = os.path.join(os.path.dirname(__file__), "Logo.png")
    with open(logo_path, "rb") as f:
        return f.read()


def get_user_market_data(user_id: int, market_df: pd.DataFrame,
                         user_commodities_df: pd.DataFrame) -> pd.DataFrame:
    """Get market data for a specific user's tracked commodities."""
    user_commodities = user_commodities_df[user_commodities_df["user_id"] == user_id]
    user_symbols = user_commodities["symbol"].tolist()

    user_market_data = market_df[market_df["symbol"].isin(user_symbols)]

    sorted_data = user_market_data.sort_values("recorded_at")
    open_records = sorted_data.groupby("symbol").first().reset_index()[
        ["symbol", "price"]]
    open_records = open_records.rename(columns={"price": "open_price_calc"})

    close_records = sorted_data.groupby("symbol").last().reset_index()
    close_records = close_records.rename(columns={"price": "close_price"})

    merged = close_records.merge(open_records, on="symbol", how="left")
    merged = merged.merge(
        user_commodities[["symbol", "buy_price", "sell_price"]],
        on="symbol",
        how="left"
    )

    return merged


def format_name(name: str) -> str:
    """Format username to display name (alice_jones -> Alice Jones)."""
    return name.replace("_", " ").title()


def generate_price_chart(symbol: str, commodity_name: str,
                         market_df: pd.DataFrame) -> tuple[str, bytes] | None:
    """Generate a price chart for a commodity and return as (cid, bytes)."""
    commodity_data = market_df[market_df["symbol"] == symbol].copy()
    commodity_data = commodity_data.sort_values("recorded_at")

    if len(commodity_data) < 2:
        return None

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 4))

    times = pd.to_datetime(commodity_data["recorded_at"])
    prices = commodity_data["price"]

    color = "#28a745" if prices.iloc[-1] >= prices.iloc[0] else "#dc3545"

    ax.plot(times, prices, color=color, linewidth=2.5)
    ax.fill_between(times, prices.min(), prices, alpha=0.2, color=color)

    price_range = prices.max() - prices.min()
    padding = price_range * 0.1 if price_range > 0 else prices.mean() * 0.01
    ax.set_ylim(prices.min() - padding, prices.max() + padding)

    ax.set_title(f"{commodity_name} ({symbol}) - Price Throughout Day",
                 fontsize=14, fontweight='bold')
    ax.set_xlabel("")
    ax.set_ylabel("Price ($)", fontsize=12)
    ax.tick_params(axis='both', labelsize=10)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.xticks(rotation=45)

    start_price = prices.iloc[0]
    end_price = prices.iloc[-1]
    
    # Avoid division by zero if start_price is 0
    if start_price != 0:
        change_pct = ((end_price - start_price) / start_price) * 100
        change_symbol = "+" if change_pct >= 0 else ""
        ax.annotate(f'{change_symbol}{change_pct:.2f}%',
                    xy=(times.iloc[-1], end_price),
                    fontsize=12, fontweight='bold', color=color)
    else:
        # Show absolute change when percentage can't be calculated
        change = end_price - start_price
        change_symbol = "+" if change >= 0 else ""
        ax.annotate(f'{change_symbol}${change:.2f}',
                    xy=(times.iloc[-1], end_price),
                    fontsize=12, fontweight='bold', color=color)

    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    image_bytes = buffer.read()
    plt.close(fig)

    cid = f"chart_{symbol.replace('/', '_')}"
    return (cid, image_bytes)


def calculate_profit_loss(row: pd.Series) -> dict:
    """Calculate profit/loss for a commodity based on buy price."""
    if pd.isna(row.get("buy_price")) or row.get("buy_price") == 0:
        return {"profit_loss": None, "profit_loss_pct": None}

    current_price = row["close_price"]
    buy_price = row["buy_price"]
    profit_loss = current_price - buy_price
    profit_loss_pct = (profit_loss / buy_price) * 100

    return {"profit_loss": profit_loss, "profit_loss_pct": profit_loss_pct}


def generate_user_html_report(user_name: str, user_data: pd.DataFrame,
                              report_date, market_df: pd.DataFrame) -> dict:
    """Generate HTML report for a single user. Returns dict with html and images."""

    rows_html = ""
    charts_html = ""
    images = {}

    for _, row in user_data.iterrows():
        pl = calculate_profit_loss(row)

        change = row["close_price"] - row["open_price_calc"]
        change_pct = (change / row["open_price_calc"]) * 100
        change_color = "#28a745" if change >= 0 else "#dc3545"
        change_symbol = "+" if change >= 0 else ""

        pl_html = "-"
        if pl["profit_loss"] is not None:
            pl_color = "#28a745" if pl["profit_loss"] >= 0 else "#dc3545"
            pl_symbol = "+" if pl["profit_loss"] >= 0 else ""
            pl_html = f'<span style="color: {pl_color}; font-weight: bold;">{pl_symbol}${pl["profit_loss"]:.2f} ({pl_symbol}{pl["profit_loss_pct"]:.2f}%)</span>'

        rows_html += f"""
        <tr>
            <td style="padding: 12px 10px; border-bottom: 1px solid #eee;"><strong>{row['commodity_name']}</strong><br><small style="color: #666;">{row['symbol']}</small></td>
            <td style="padding: 12px 10px; border-bottom: 1px solid #eee;">${row['open_price_calc']:.2f}</td>
            <td style="padding: 12px 10px; border-bottom: 1px solid #eee;">${row['close_price']:.2f}</td>
            <td style="padding: 12px 10px; border-bottom: 1px solid #eee; color: {change_color}; font-weight: bold;">{change_symbol}{change:.2f} ({change_symbol}{change_pct:.2f}%)</td>
            <td style="padding: 12px 10px; border-bottom: 1px solid #eee;">${row['day_low']:.2f}</td>
            <td style="padding: 12px 10px; border-bottom: 1px solid #eee;">${row['day_high']:.2f}</td>
            <td style="padding: 12px 10px; border-bottom: 1px solid #eee;">{int(row['volume']):,}</td>
            <td style="padding: 12px 10px; border-bottom: 1px solid #eee;">{pl_html}</td>
        </tr>
        """

        chart_result = generate_price_chart(
            row['symbol'], row['commodity_name'], market_df)
        if chart_result:
            cid, img_bytes = chart_result
            images[cid] = img_bytes
            charts_html += f'<div style="margin: 15px 0; padding: 10px; border-bottom: 1px solid #eee;"><img src="cid:{cid}" alt="{row["commodity_name"]} price chart" style="max-width:100%;"/></div>'

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Daily Commodities Report - {report_date}</title>
</head>
<body style="font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background: white; border-radius: 10px; margin-bottom: 20px;">
        <tr>
            <td style="padding: 30px;">
                <table cellpadding="0" cellspacing="0">
                    <tr>
                        <td style="vertical-align: middle; padding-right: 20px;">
                            <img src="cid:logo" alt="Pivot Point Logo" width="80" height="80" style="display: block; width: 80px; height: 80px; max-width: 80px;"/>
                        </td>
                        <td style="vertical-align: middle;">
                            <h1 style="margin: 0 0 10px 0; color: #333;">📊 Daily Commodities Report</h1>
                            <p style="margin: 5px 0; color: #333;">Hello, {format_name(user_name)}!</p>
                            <p style="margin: 5px 0; color: #333;">Report Date: {report_date.strftime('%B %d, %Y')}</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
    
    <table width="100%" cellpadding="0" cellspacing="0" style="background: white; border-radius: 10px; margin-bottom: 20px;">
        <tr>
            <td style="padding: 20px;">
                <h3 style="margin: 0 0 10px 0; color: #333;">Your Tracked Commodities</h3>
                <p style="margin: 0; color: #333;">You are tracking <strong>{len(user_data)}</strong> commodities.</p>
            </td>
        </tr>
    </table>
    
    <table width="100%" cellpadding="0" cellspacing="0" style="background: white; border-radius: 10px; border-collapse: collapse;">
        <tr style="background: #F7941D;">
            <th style="padding: 15px 10px; text-align: left; color: white; font-weight: bold;">Commodity</th>
            <th style="padding: 15px 10px; text-align: left; color: white; font-weight: bold;">Open</th>
            <th style="padding: 15px 10px; text-align: left; color: white; font-weight: bold;">Close</th>
            <th style="padding: 15px 10px; text-align: left; color: white; font-weight: bold;">Change</th>
            <th style="padding: 15px 10px; text-align: left; color: white; font-weight: bold;">Low</th>
            <th style="padding: 15px 10px; text-align: left; color: white; font-weight: bold;">High</th>
            <th style="padding: 15px 10px; text-align: left; color: white; font-weight: bold;">Volume</th>
            <th style="padding: 15px 10px; text-align: left; color: white; font-weight: bold;">P/L</th>
        </tr>
        {rows_html}
    </table>
    
    <table width="100%" cellpadding="0" cellspacing="0" style="background: white; border-radius: 10px; margin-top: 20px;">
        <tr>
            <td style="padding: 20px;">
                <h3 style="margin: 0 0 15px 0; color: #1DAEEC;">📈 Price Charts</h3>
                {charts_html}
            </td>
        </tr>
    </table>
    
    <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
            <td style="padding: 20px; text-align: center; color: #666; font-size: 12px;">
                <p style="margin: 5px 0;">This report was automatically generated by Pivot Point.</p>
                <p style="margin: 5px 0;">Data as of {report_date}</p>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    return {"html": html, "images": images}


def generate_all_user_reports() -> dict:
    """Generate HTML reports for all users with tracked commodities."""
    report_date = get_previous_day_date()
    user_commodities_df = extract_user_commodities()
    market_df = extract_market_records()

    if market_df.empty:
        print(f"No market data found for {report_date}")
        return {}

    users = user_commodities_df[["user_id",
                                 "user_name", "email"]].drop_duplicates()

    reports = {}
    for _, user in users.iterrows():
        user_id = user["user_id"]
        user_name = user["user_name"]
        email = user["email"]

        user_data = get_user_market_data(
            user_id, market_df, user_commodities_df)

        if user_data.empty:
            print(f"No market data for user {user_name}")
            continue

        reports[email] = generate_user_html_report(
            user_name, user_data, report_date, market_df)
        print(f"Generated report for {user_name}")

    return reports


def send_email(ses_client, sender: str, recipient: str, report_data: dict) -> bool:
    """Send email via SES with embedded images using MIME."""
    try:
        msg = MIMEMultipart('related')
        msg['Subject'] = "Your Daily Commodity Report - Pivot Point"
        msg['From'] = sender
        msg['To'] = recipient

        html_part = MIMEText(report_data["html"], 'html')
        msg.attach(html_part)

        logo_img = MIMEImage(get_logo_bytes())
        logo_img.add_header('Content-ID', '<logo>')
        logo_img.add_header('Content-Disposition',
                            'inline', filename='logo.png')
        msg.attach(logo_img)

        for cid, img_bytes in report_data["images"].items():
            img = MIMEImage(img_bytes)
            img.add_header('Content-ID', f'<{cid}>')
            img.add_header('Content-Disposition',
                           'inline', filename=f'{cid}.png')
            msg.attach(img)

        ses_client.send_raw_email(
            Source=sender,
            Destinations=[recipient],
            RawMessage={'Data': msg.as_string()}
        )
        print(f"Email sent to {recipient}")
        return True
    except Exception as e:
        print(f"Failed to send email to {recipient}: {e}")
        return False


def handler(event, context):
    """AWS Lambda handler function."""
    print(f"Generating reports for: {get_previous_day_date()}")
    reports = generate_all_user_reports()

    if not reports:
        print("No reports generated.")
        return {"statusCode": 200, "emailsSent": 0}

    print(f"Generated {len(reports)} reports.")

    sender_email = os.environ.get("SENDER_EMAIL")
    if not sender_email:
        print("ERROR: SENDER_EMAIL environment variable not set")
        return {"statusCode": 500, "error": "SENDER_EMAIL not configured"}

    ses_client = boto3.client("ses", region_name="eu-west-2")
    emails_sent = 0

    for email, report_data in reports.items():
        if send_email(ses_client, sender_email, email, report_data):
            emails_sent += 1

    print(f"Sent {emails_sent}/{len(reports)} emails.")
    return {"statusCode": 200, "emailsSent": emails_sent}
