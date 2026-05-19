"""Gmail via SMTP + App Password — no OAuth, no Google Cloud project needed."""
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def _clean_password(app_password: str) -> str:
    """Remove spaces from app password — Google shows it as 'xxxx xxxx xxxx xxxx' but SMTP needs no spaces."""
    return app_password.replace(" ", "").strip()


def send_email(gmail_user: str, app_password: str, to: str,
               subject: str, html_body: str) -> tuple:
    """Send an email using Gmail SMTP with an App Password.
    `to` may be comma- or semicolon-separated for multiple recipients.
    Returns (success: bool, error_message: str).
    """
    pwd = _clean_password(app_password)
    # Split on comma or semicolon, strip whitespace, drop empties
    recipients = [r.strip() for r in to.replace(";", ",").split(",") if r.strip()]
    if not recipients:
        return False, "No valid recipient email addresses"
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = gmail_user
        msg["To"] = ", ".join(recipients)   # RFC-compliant header
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.login(gmail_user, pwd)
            server.sendmail(gmail_user, recipients, msg.as_string())  # list of addresses

        logger.info(f"Email sent to {to}: {subject}")
        return True, ""
    except smtplib.SMTPAuthenticationError:
        msg = "Gmail authentication failed — re-enter your App Password in Settings"
        logger.error(msg)
        return False, msg
    except smtplib.SMTPException as e:
        msg = f"SMTP error: {e}"
        logger.error(msg)
        return False, msg
    except Exception as e:
        msg = f"Send failed: {e}"
        logger.error(msg)
        return False, msg


def test_connection(gmail_user: str, app_password: str) -> tuple[bool, str]:
    """Test SMTP credentials. Returns (success, message)."""
    pwd = _clean_password(app_password)
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.login(gmail_user, pwd)
        return True, "Connected successfully"
    except smtplib.SMTPAuthenticationError:
        return False, "Authentication failed — wrong Gmail address or App Password"
    except Exception as e:
        return False, str(e)


# Kept for compatibility with scheduler — maps old signature to new
def is_authorized(token_file: str = "") -> bool:
    return False  # Not used with App Password approach
