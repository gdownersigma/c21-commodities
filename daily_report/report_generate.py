"""Script to generate HTML reports for each user from extracted data."""
import os
import base64
from io import BytesIO
import boto3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from report_extract import (
    get_previous_day_date,
    extract_user_commodities,
    extract_market_records,
)


def get_logo_base64() -> str:
    """Load logo and return as base64 encoded string."""
    logo_path = os.path.join(os.path.dirname(__file__), "Logo.png")
    with open(logo_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')


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
                         market_df: pd.DataFrame) -> str:
    """Generate a price chart for a commodity and return as base64 image."""
    commodity_data = market_df[market_df["symbol"] == symbol].copy()
    commodity_data = commodity_data.sort_values("recorded_at")

    if len(commodity_data) < 2:
        return ""

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
    if start_price == 0:
        # Avoid division by zero; treat change as 0% when starting price is zero.
        change_pct = 0.0
    else:
        change_pct = ((end_price - start_price) / start_price) * 100
    change_symbol = "+" if change_pct >= 0 else ""
    ax.annotate(f'{change_symbol}{change_pct:.2f}%',
                xy=(times.iloc[-1], end_price),
                fontsize=12, fontweight='bold', color=color)

    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close(fig)

    return f'<img src="data:image/png;base64,{image_base64}" alt="{commodity_name} price chart" style="max-width:100%; margin: 10px 0;">'


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
                              report_date, market_df: pd.DataFrame) -> str:
    """Generate HTML report for a single user."""

    rows_html = ""
    charts_html = ""
    for _, row in user_data.iterrows():
        pl = calculate_profit_loss(row)

        change = row["close_price"] - row["open_price_calc"]
        change_pct = (change / row["open_price_calc"]) * 100
        change_class = "positive" if change >= 0 else "negative"
        change_symbol = "+" if change >= 0 else ""

        pl_html = "-"
        if pl["profit_loss"] is not None:
            pl_class = "positive" if pl["profit_loss"] >= 0 else "negative"
            pl_symbol = "+" if pl["profit_loss"] >= 0 else ""
            pl_html = f'<span class="{pl_class}">{pl_symbol}${pl["profit_loss"]:.2f} ({pl_symbol}{pl["profit_loss_pct"]:.2f}%)</span>'

        rows_html += f"""
        <tr>
            <td><strong>{row['commodity_name']}</strong><br><small>{row['symbol']}</small></td>
            <td>${row['open_price_calc']:.2f}</td>
            <td>${row['close_price']:.2f}</td>
            <td class="{change_class}">{change_symbol}{change:.2f} ({change_symbol}{change_pct:.2f}%)</td>
            <td>${row['day_low']:.2f}</td>
            <td>${row['day_high']:.2f}</td>
            <td>{int(row['volume']):,}</td>
            <td>{pl_html}</td>
        </tr>
        """

        chart = generate_price_chart(
            row['symbol'], row['commodity_name'], market_df)
        if chart:
            charts_html += f'<div class="chart-container">{chart}</div>'

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Daily Commodities Report - {report_date}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: white;
            color: #333;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header-logo {{
            width: 120px;
            height: 120px;
            flex-shrink: 0;
        }}
        .header-content {{
            flex-grow: 1;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
        }}
        .header p {{
            margin: 5px 0;
            opacity: 0.9;
        }}
        .summary {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th {{
            background: #F7941D;
            color: white;
            padding: 15px 10px;
            text-align: left;
        }}
        td {{
            padding: 12px 10px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .positive {{
            color: #28a745;
            font-weight: bold;
        }}
        .negative {{
            color: #dc3545;
            font-weight: bold;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 12px;
        }}
        .charts-section {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .charts-section h3 {{
            margin-top: 0;
            color: #1DAEEC;
        }}
        .chart-container {{
            margin: 15px 0;
            padding: 10px;
            border-bottom: 1px solid #eee;
        }}
        .chart-container:last-child {{
            border-bottom: none;
        }}
    </style>
</head>
<body>
    <div class="header">
        <img class="header-logo" src="data:image/png;base64,{get_logo_base64()}" alt="Pivot Point Logo"/>
        <div class="header-content">
            <h1>📊 Daily Commodities Report</h1>
            <p>Hello, {format_name(user_name)}!</p>
            <p>Report Date: {report_date.strftime('%B %d, %Y')}</p>
        </div>
    </div>
    
    <div class="summary">
        <h3>Your Tracked Commodities</h3>
        <p>You are tracking <strong>{len(user_data)}</strong> commodities.</p>
    </div>
    
    <table>
        <thead>
            <tr>
                <th>Commodity</th>
                <th>Open Price</th>
                <th>Close Price</th>
                <th>Change</th>
                <th>Day Low</th>
                <th>Day High</th>
                <th>Volume</th>
                <th>Potential P/L</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    
    <div class="charts-section">
        <h3>📈 Price Charts</h3>
        {charts_html}
    </div>
    
    <div class="footer">
        <p>This report was automatically generated by Pivot Point.</p>
        <p>Data as of {report_date}</p>
    </div>
</body>
</html>
"""
    return html


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


def send_email(ses_client, sender: str, recipient: str, html: str) -> bool:
    """Send email via SES."""
    try:
        ses_client.send_email(
            Source=sender,
            Destination={"ToAddresses": [recipient]},
            Message={
                "Subject": {
                    "Data": "Your Daily Commodity Report - Pivot Point",
                    "Charset": "UTF-8"
                },
                "Body": {
                    "Html": {
                        "Data": html,
                        "Charset": "UTF-8"
                    }
                }
            }
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

    for email, html in reports.items():
        if send_email(ses_client, sender_email, email, html):
            emails_sent += 1

    print(f"Sent {emails_sent}/{len(reports)} emails.")
    return {"statusCode": 200, "emailsSent": emails_sent}
