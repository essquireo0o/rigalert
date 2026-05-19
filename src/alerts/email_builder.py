from datetime import datetime
from typing import List
from ..core.miner import MinerData


def build_summary_email(miners: List[MinerData], interval_label: str, farm_name: str = "") -> tuple[str, str]:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = len(miners)
    online = sum(1 for m in miners if m.status == "online")
    warning = sum(1 for m in miners if m.status == "warning")
    offline = sum(1 for m in miners if m.status == "offline")
    unknown = total - online - warning - offline

    total_ths = sum(m.best_hashrate() for m in miners if m.status != "offline")
    problems = [m for m in miners if m.status in ("offline", "warning", "error") or m.alerts]

    farm_prefix = f"[{farm_name}] " if farm_name else ""
    subject = f"{farm_prefix}RigAlert™ {interval_label} Report — {online}/{total} Online"
    if problems:
        subject += f" | {len(problems)} Issues"

    # Color palette
    C_BG = "#0d1117"
    C_CARD = "#161b22"
    C_BORDER = "#30363d"
    C_ORANGE = "#c8a94b"
    C_GREEN = "#3fb950"
    C_YELLOW = "#d29922"
    C_RED = "#f85149"
    C_TEXT = "#e6edf3"
    C_MUTED = "#8b949e"

    def status_badge(status: str) -> str:
        if status == "online":
            return f'<span style="background:{C_GREEN};color:#000;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:bold;">ONLINE</span>'
        if status == "warning":
            return f'<span style="background:{C_YELLOW};color:#000;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:bold;">WARNING</span>'
        if status == "offline":
            return f'<span style="background:{C_RED};color:#fff;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:bold;">OFFLINE</span>'
        return f'<span style="background:{C_BORDER};color:{C_TEXT};padding:2px 8px;border-radius:12px;font-size:11px;">UNKNOWN</span>'

    # Summary cards
    summary_cards = f"""
    <table width="100%" cellpadding="0" cellspacing="12" style="margin-bottom:24px;">
      <tr>
        <td width="25%">
          <div style="background:{C_CARD};border:1px solid {C_BORDER};border-top:3px solid {C_GREEN};
               border-radius:8px;padding:16px;text-align:center;">
            <div style="font-size:32px;font-weight:bold;color:{C_GREEN};">{online}</div>
            <div style="color:{C_MUTED};font-size:12px;margin-top:4px;">ONLINE</div>
          </div>
        </td>
        <td width="25%">
          <div style="background:{C_CARD};border:1px solid {C_BORDER};border-top:3px solid {C_RED};
               border-radius:8px;padding:16px;text-align:center;">
            <div style="font-size:32px;font-weight:bold;color:{C_RED};">{offline}</div>
            <div style="color:{C_MUTED};font-size:12px;margin-top:4px;">OFFLINE</div>
          </div>
        </td>
        <td width="25%">
          <div style="background:{C_CARD};border:1px solid {C_BORDER};border-top:3px solid {C_YELLOW};
               border-radius:8px;padding:16px;text-align:center;">
            <div style="font-size:32px;font-weight:bold;color:{C_YELLOW};">{warning}</div>
            <div style="color:{C_MUTED};font-size:12px;margin-top:4px;">WARNINGS</div>
          </div>
        </td>
        <td width="25%">
          <div style="background:{C_CARD};border:1px solid {C_BORDER};border-top:3px solid {C_ORANGE};
               border-radius:8px;padding:16px;text-align:center;">
            <div style="font-size:32px;font-weight:bold;color:{C_ORANGE};">{total_ths:.1f}</div>
            <div style="color:{C_MUTED};font-size:12px;margin-top:4px;">TOTAL TH/s</div>
          </div>
        </td>
      </tr>
    </table>
    """

    # Issues section
    issues_html = ""
    if problems:
        rows = ""
        for m in problems:
            issue_list = "<br>".join(m.alerts) if m.alerts else ("Offline" if m.status == "offline" else "")
            bc = C_RED if m.status == "offline" else C_YELLOW
            rows += f"""
            <tr style="border-bottom:1px solid {C_BORDER};">
              <td style="padding:10px 12px;color:{C_TEXT};">{status_badge(m.status)}</td>
              <td style="padding:10px 12px;color:{C_TEXT};font-weight:bold;">{m.display_name}</td>
              <td style="padding:10px 12px;color:{C_MUTED};font-family:monospace;">{m.ip}</td>
              <td style="padding:10px 12px;color:{C_ORANGE};">{m.display_hashrate()}</td>
              <td style="padding:10px 12px;color:{m.display_temp() and C_TEXT or C_MUTED};">{m.display_temp()}</td>
              <td style="padding:10px 12px;color:{bc};font-size:12px;">{issue_list}</td>
            </tr>
            """
        issues_html = f"""
        <h2 style="color:{C_RED};font-size:16px;margin:24px 0 12px;">Issues Detected ({len(problems)})</h2>
        <table width="100%" cellpadding="0" cellspacing="0"
               style="border-collapse:collapse;border:1px solid {C_BORDER};border-radius:8px;overflow:hidden;">
          <thead>
            <tr style="background:{C_CARD};">
              <th style="padding:10px 12px;text-align:left;color:{C_MUTED};font-size:11px;font-weight:600;">STATUS</th>
              <th style="padding:10px 12px;text-align:left;color:{C_MUTED};font-size:11px;font-weight:600;">NAME</th>
              <th style="padding:10px 12px;text-align:left;color:{C_MUTED};font-size:11px;font-weight:600;">IP</th>
              <th style="padding:10px 12px;text-align:left;color:{C_MUTED};font-size:11px;font-weight:600;">HASHRATE</th>
              <th style="padding:10px 12px;text-align:left;color:{C_MUTED};font-size:11px;font-weight:600;">TEMP</th>
              <th style="padding:10px 12px;text-align:left;color:{C_MUTED};font-size:11px;font-weight:600;">ISSUES</th>
            </tr>
          </thead>
          <tbody style="background:{C_BG};">
            {rows}
          </tbody>
        </table>
        """

    # All miners table
    all_rows = ""
    for m in sorted(miners, key=lambda x: (x.status != "offline", x.display_name)):
        all_rows += f"""
        <tr style="border-bottom:1px solid {C_BORDER};">
          <td style="padding:8px 10px;">{status_badge(m.status)}</td>
          <td style="padding:8px 10px;color:{C_TEXT};font-weight:500;">{m.display_name}</td>
          <td style="padding:8px 10px;color:{C_MUTED};font-family:monospace;font-size:12px;">{m.ip}</td>
          <td style="padding:8px 10px;color:{C_ORANGE};font-weight:bold;">{m.display_hashrate()}</td>
          <td style="padding:8px 10px;color:{C_TEXT};">{m.display_temp()}</td>
          <td style="padding:8px 10px;color:{C_TEXT};">{m.display_fan()}</td>
          <td style="padding:8px 10px;color:{C_TEXT};">{m.display_uptime()}</td>
          <td style="padding:8px 10px;color:{C_MUTED};font-size:11px;max-width:200px;word-break:break-all;">{m.pool_url[:40] + "..." if len(m.pool_url) > 40 else m.pool_url}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>RigAlert™ by ING Mining Report</title></head>
<body style="margin:0;padding:0;background:{C_BG};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0">
  <tr><td>
    <table width="640" cellpadding="0" cellspacing="0" align="center" style="margin:24px auto;">
      <tr>
        <td style="background:{C_CARD};border:1px solid {C_BORDER};border-radius:12px;padding:32px;">

          <!-- Header -->
          <div style="margin-bottom:24px;border-bottom:1px solid {C_BORDER};padding-bottom:20px;">
            <div style="display:inline-block;">
              <span style="font-size:22px;font-weight:700;color:{C_ORANGE};">⛏ RigAlert™ by ING Mining</span>
              {f'<span style="font-size:14px;color:{C_TEXT};font-weight:600;margin-left:10px;">— {farm_name}</span>' if farm_name else ''}
              <span style="font-size:14px;color:{C_MUTED};margin-left:12px;">{interval_label} Report</span>
            </div>
            <div style="color:{C_MUTED};font-size:12px;margin-top:6px;">{now}</div>
          </div>

          <!-- Summary Cards -->
          {summary_cards}

          <!-- Issues -->
          {issues_html}

          <!-- All Miners -->
          <h2 style="color:{C_TEXT};font-size:16px;margin:24px 0 12px;">All Miners ({total})</h2>
          <table width="100%" cellpadding="0" cellspacing="0"
                 style="border-collapse:collapse;border:1px solid {C_BORDER};border-radius:8px;overflow:hidden;font-size:13px;">
            <thead>
              <tr style="background:{C_CARD};">
                <th style="padding:8px 10px;text-align:left;color:{C_MUTED};font-size:11px;">STATUS</th>
                <th style="padding:8px 10px;text-align:left;color:{C_MUTED};font-size:11px;">NAME</th>
                <th style="padding:8px 10px;text-align:left;color:{C_MUTED};font-size:11px;">IP</th>
                <th style="padding:8px 10px;text-align:left;color:{C_MUTED};font-size:11px;">HASHRATE</th>
                <th style="padding:8px 10px;text-align:left;color:{C_MUTED};font-size:11px;">TEMP</th>
                <th style="padding:8px 10px;text-align:left;color:{C_MUTED};font-size:11px;">FAN</th>
                <th style="padding:8px 10px;text-align:left;color:{C_MUTED};font-size:11px;">UPTIME</th>
                <th style="padding:8px 10px;text-align:left;color:{C_MUTED};font-size:11px;">POOL</th>
              </tr>
            </thead>
            <tbody style="background:{C_BG};">
              {all_rows}
            </tbody>
          </table>

          <!-- Footer -->
          <div style="margin-top:24px;padding-top:16px;border-top:1px solid {C_BORDER};
                      color:{C_MUTED};font-size:11px;text-align:center;">
            RigAlert™ by ING Mining — Bitcoin Miner Monitor &nbsp;|&nbsp; {now}
          </div>

        </td>
      </tr>
    </table>
  </td></tr>
</table>
</body>
</html>"""

    return subject, html
