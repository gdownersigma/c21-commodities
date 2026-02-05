"""Function to generate price alert html for commodities."""
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage


def get_logo_bytes() -> bytes:
    """Load logo and return as bytes."""
    logo_path = os.path.join(os.path.dirname(__file__), "Logo.png")
    with open(logo_path, "rb") as f:
        return f.read()


def generate_alert_email(alert: dict) -> str:
    """Generate HTML email for price alert"""

    alert_color = "#22c55e" if alert['alert_type'] == "buy" else "#ef4444"
    alert_label = "BUY" if alert['alert_type'] == "buy" else "SELL"
    accent_color = "#03c1ff" if alert['alert_type'] == "buy" else "#e6530c"
    formatted_name = alert['user_name'].split('_')[0].capitalize()

    html = f"""<!DOCTYPE html>
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4; padding: 40px 0;">
    <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.3);">
                    
                    <!-- Header with Gradient -->
                    <tr>
                        <td style="background-color: #ffffff; padding: 30px 30px 20px; text-align: center; border-bottom: 2px solid #e2e8f0;">
                            <img src="cid:logo" alt="Pivot Point Logo" style="max-width: 200px; height: auto;">
                        </td>
                    </tr>
                    
                    <!-- Alert Badge with Icon -->
                    <tr>
                        <td style="padding: 40px 30px 20px; text-align: center; background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);">
                            <div style="display: inline-block; background-color: {alert_color}; color: white; padding: 12px 28px; border-radius: 30px; font-weight: bold; font-size: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); letter-spacing: 1px;">
                                {alert_label} ALERT TRIGGERED
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Commodity Info with Accent Border -->
                    <tr>
                        <td style="padding: 20px 30px;">
                            <div style="background: linear-gradient(135deg, {accent_color}15 0%, {accent_color}05 100%); border-left: 4px solid {accent_color}; border-radius: 8px; padding: 20px; text-align: center;">
                                <h2 style="color: #1e293b; margin: 0 0 8px 0; font-size: 28px; font-weight: 700;">{alert['commodity_name']}</h2>
                                <p style="color: #64748b; margin: 0; font-size: 16px; font-weight: 600;">
                                    <span style="background-color: {accent_color}20; color: {accent_color}; padding: 4px 12px; border-radius: 12px;">
                                        {alert['symbol']}
                                    </span>
                                </p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Greeting -->
                    <tr>
                        <td style="padding: 20px 30px 10px;">
                            <p style="font-size: 18px; color: #333; margin: 0; font-weight: 600;">Hi {formatted_name} 👋</p>
                        </td>
                    </tr>
                    
                    <!-- Message -->
                    <tr>
                        <td style="padding: 10px 30px 20px;">
                            <p style="font-size: 16px; color: #475569; margin: 0; line-height: 1.6;">
                                Great news! Your price alert has been triggered. Check out the details below:
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Price Cards -->
                    <tr>
                        <td style="padding: 0 30px 30px;">
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td width="48%" style="vertical-align: top;">
                                        <div style="background: linear-gradient(135deg, {accent_color}10 0%, {accent_color}05 100%); border-radius: 12px; padding: 20px; text-align: center; border: 2px solid {accent_color}30;">
                                            <p style="color: #64748b; font-size: 13px; margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">Current Price</p>
                                            <p style="color: {accent_color}; font-size: 32px; font-weight: 700; margin: 0; line-height: 1;">${alert['current_price']:.2f}</p>
                                        </div>
                                    </td>
                                    <td width="4%"></td>
                                    <td width="48%" style="vertical-align: top;">
                                        <div style="background-color: #f1f5f9; border-radius: 12px; padding: 20px; text-align: center; border: 2px solid #e2e8f0;">
                                            <p style="color: #64748b; font-size: 13px; margin: 0 0 8px 0; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600;">Target Price</p>
                                            <p style="color: #334155; font-size: 32px; font-weight: 700; margin: 0; line-height: 1;">${alert['target_price']:.2f}</p>
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- CTA Button -->
                    <tr>
                        <td style="padding: 0 30px 40px; text-align: center;">
                            <a href="#" style="display: inline-block; background-color: #03c1ff; color: white; text-decoration: none; padding: 14px 40px; border-radius: 30px; font-weight: bold; font-size: 16px; box-shadow: 0 6px 20px rgba(3, 193, 255, 0.3); transition: all 0.3s;">
                                View Dashboard →
                            </a>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); padding: 30px; text-align: center; border-top: 1px solid #cbd5e1;">
                            <p style="font-size: 13px; color: #64748b; margin: 0 0 8px 0; line-height: 1.5;">
                                You received this email because you set up a price alert on Pivot Point.
                            </p>
                            <p style="font-size: 12px; color: #94a3b8; margin: 0;">
                                &copy; 2026 Pivot Point. All rights reserved.
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    return html


def save_test_email(alert: dict, filename: str = "test_email.html"):
    """Save email HTML to file for testing with relative logo path"""
    html = generate_alert_email(alert)

    # Replace cid:logo with relative file path for testing
    html = html.replace('src="cid:logo"', 'src="Logo.png"')

    with open(filename, "w") as f:
        f.write(html)
    print(f"Saved to {filename}")
