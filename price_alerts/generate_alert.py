"""Function to generate price alert html for commodities."""
import os


def get_logo_bytes() -> bytes:
    """Load logo and return as bytes."""
    logo_path = os.path.join(os.path.dirname(__file__), "Logo.png")
    with open(logo_path, "rb") as f:
        return f.read()


def load_email_template() -> str:
    """Load the HTML email template from file."""
    template_path = os.path.join(
        os.path.dirname(__file__), "alert_template.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def generate_alert_email(alert: dict) -> str:
    """Generate HTML email for price alert"""

    alert_color = "#22c55e" if alert['alert_type'] == "buy" else "#ef4444"
    alert_label = "BUY" if alert['alert_type'] == "buy" else "SELL"
    accent_color = "#03c1ff" if alert['alert_type'] == "buy" else "#e6530c"
    formatted_name = alert['user_name'].split('_')[0].capitalize()

    html = load_email_template()
    html = html.format(
        alert_color=alert_color,
        alert_label=alert_label,
        accent_color=accent_color,
        commodity_name=alert['commodity_name'],
        symbol=alert['symbol'],
        formatted_name=formatted_name,
        current_price=f"{alert['current_price']:.2f}",
        target_price=f"{alert['target_price']:.2f}"
    )

    return html


def save_test_email(alert: dict, filename: str = "test_email.html"):
    """Save email HTML to file for testing with relative logo path"""
    html = generate_alert_email(alert)

    # Replace cid:logo with relative file path for testing
    html = html.replace('src="cid:logo"', 'src="Logo.png"')

    with open(filename, "w") as f:
        f.write(html)
    print(f"Saved to {filename}")
