"""
Licensing hook for future Stripe-based monetization.

Currently a no-op — license_enabled defaults to False in AppConfig.
To activate: set license_enabled=True and populate stripe_secret_key
in rigalert_config.json (which is gitignored — never commit keys).

Stripe integration points:
  - validate_license(cfg)  : call on app startup; returns (ok, message)
  - create_checkout(cfg)   : open Stripe checkout in browser (future)
  - get_customer_portal(cfg): open billing portal in browser (future)

How to wire up a paid tier later:
  1. Create a Stripe product + price in the dashboard
  2. Generate a license key per customer (metadata on the Stripe subscription)
  3. Set stripe_secret_key in the config (or seed_config for bundled EXEs)
  4. Set license_enabled = True
  5. validate_license() will verify the key against the Stripe API
"""

import logging

logger = logging.getLogger(__name__)


def validate_license(cfg) -> tuple[bool, str]:
    """Check the license key against Stripe. Returns (valid, message).

    When license_enabled is False this always returns (True, "unlicensed mode")
    so the app works normally for free/internal use.
    """
    if not getattr(cfg, "license_enabled", False):
        return True, "unlicensed mode"

    secret_key = getattr(cfg, "stripe_secret_key", "").strip()
    license_key = getattr(cfg, "license_key", "").strip()

    if not secret_key:
        logger.warning("License enabled but stripe_secret_key not set — allowing access")
        return True, "no Stripe key configured"

    if not license_key:
        return False, "No license key entered. Please enter your license key in Settings."

    try:
        import urllib.request, json, base64
        auth = base64.b64encode(f"{secret_key}:".encode()).decode()
        # Search for a customer or subscription with this metadata key
        url = f"https://api.stripe.com/v1/customers/search?query=metadata%5B%27license_key%27%5D%3A%27{license_key}%27"
        req = urllib.request.Request(url, headers={"Authorization": f"Basic {auth}"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        customers = data.get("data", [])
        if customers:
            logger.info("License validated for customer: %s", customers[0].get("email", ""))
            return True, f"Licensed to {customers[0].get('email', 'verified customer')}"
        return False, "License key not found. Contact support@ingmining.com."
    except Exception as exc:
        logger.warning("License check failed (network?): %s — allowing access", exc)
        return True, "License check skipped (offline)"


def open_checkout(cfg, price_id: str = ""):
    """Open a Stripe checkout page in the default browser.
    Wire this to a 'Buy License' button when you're ready to sell.
    price_id comes from your Stripe dashboard (price_XXXX).
    """
    import webbrowser
    publishable_key = getattr(cfg, "stripe_publishable_key", "").strip()
    if not publishable_key or not price_id:
        webbrowser.open("https://ingmining.com")
        return
    # In production: generate a Stripe Checkout Session server-side and redirect.
    # For a simple one-time payment you can also use a Payment Link from the dashboard.
    webbrowser.open(f"https://buy.stripe.com/{price_id}")


def open_customer_portal(cfg, customer_email: str = ""):
    """Open the Stripe customer billing portal."""
    import webbrowser
    webbrowser.open("https://billing.stripe.com")
