"""
Telemetry — anonymous usage heartbeat for the operator dashboard.

Sends a single non-blocking HTTP POST on every app launch so you can see:
  - Total installs (unique install_ids)
  - Licensed vs unlicensed breakdown
  - Miner counts per installation (useful for tier pricing)
  - First-seen and last-seen timestamps
  - App version

OFF BY DEFAULT. Enable by setting telemetry_enabled=true and supplying
a telemetry_endpoint + telemetry_api_key in the config.

──────────────────────────────────────────────────────────────────
HOW TO SET UP THE BACKEND (Supabase — free, 5 minutes)
──────────────────────────────────────────────────────────────────
1. Create a free project at https://supabase.com
2. Open the SQL editor and run:

    create table installs (
        install_id   text primary key,
        license_key  text,
        licensed     boolean default false,
        app_version  text,
        miner_count  int default 0,
        farm_name    text,
        first_seen   timestamptz default now(),
        last_seen    timestamptz default now()
    );

    -- Allow the app to upsert rows (anon key is safe for write-only)
    alter table installs enable row level security;
    create policy "app can upsert" on installs
        for all using (true) with check (true);

3. In Supabase → Settings → API, copy:
   - Project URL  → telemetry_endpoint  (append /rest/v1/installs)
   - anon key     → telemetry_api_key

4. Set in rigalert_seed_config.json:
    "telemetry_enabled": true,
    "telemetry_endpoint": "https://xxxx.supabase.co/rest/v1/installs",
    "telemetry_api_key": "<anon key>"

5. Open https://xxxx.supabase.co → Table Editor → installs
   That IS your dashboard. You can also build a simple view with:

    select
        count(*)                                    as total_installs,
        count(*) filter (where licensed)            as licensed,
        count(*) filter (where not licensed)        as unlicensed,
        sum(miner_count)                            as total_miners_monitored,
        max(last_seen)                              as last_activity
    from installs;

──────────────────────────────────────────────────────────────────
"""

import json
import logging
import threading
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_APP_VERSION = "2.2"


def ping(cfg, license_ok: bool, miner_count: int = 0) -> None:
    """Fire-and-forget telemetry ping. Runs in a daemon thread; never blocks startup."""
    if not getattr(cfg, "telemetry_enabled", False):
        return
    endpoint = getattr(cfg, "telemetry_endpoint", "").strip()
    api_key  = getattr(cfg, "telemetry_api_key",  "").strip()
    if not endpoint or not api_key:
        return

    install_id  = getattr(cfg, "install_id",  "")
    license_key = getattr(cfg, "license_key", "")
    farm_name   = getattr(cfg, "farm_name",   "")

    payload = {
        "install_id":  install_id,
        "license_key": license_key or None,
        "licensed":    license_ok and getattr(cfg, "license_enabled", False),
        "app_version": _APP_VERSION,
        "miner_count": miner_count,
        "farm_name":   farm_name or None,
        "last_seen":   datetime.now(timezone.utc).isoformat(),
    }

    def _send():
        try:
            import urllib.request
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                endpoint,
                data=data,
                method="POST",
                headers={
                    "Content-Type":  "application/json",
                    "apikey":        api_key,
                    "Authorization": f"Bearer {api_key}",
                    # Supabase upsert on primary key (install_id)
                    "Prefer":        "resolution=merge-duplicates",
                },
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                logger.debug("Telemetry ping OK: %s", r.status)
        except Exception as exc:
            logger.debug("Telemetry ping failed (non-fatal): %s", exc)

    threading.Thread(target=_send, daemon=True).start()
