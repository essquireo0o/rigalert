# Changelog

All notable changes to RigAlert™ are documented here.

---

## [Unreleased]

### Added
- ROADMAP.md and CHANGELOG.md
- **Dashboard page** wired into sidebar nav as the first (home) tab
- **Firmware Tools page** — firmware type detection (VNish / Braiins OS / Stock), per-chain board status, safety-gated dry-run install and restore dialogs, VNish config backup via HTTP API, audit log entries for all firmware actions
- `src/core/firmware.py` — `detect_type()`, `firmware_badge_color()`, VNish HTTP helpers (`vnish_get_info`, `vnish_get_config`, `vnish_get_network`)
- **Crypto price alerts** — polls CoinGecko every 5 min (no API key), BTC above/below thresholds, ±% 24h move alerts, altcoin support (any CoinGecko coin ID), state-change deduplication (one alert per threshold cross), "Check Prices Now" button in Alerts page
- **Per-miner notes** — notes field in Add/Edit Miner dialog, stored in SQLite, shown as row tooltip in Miners table; DB migration handles existing installations
- **Miner Groups** — create/edit/delete named groups with color labels; assign miners to groups; filter Miners page by group; Groups management page (slot 5 in nav); group member detail panel
- **Fleet stats bar** on Dashboard — TH/s, total power (kW), efficiency (W/TH), estimated daily USD revenue (BTC price × fleet TH/s), online/warning/offline counts; BTC price auto-fed from PriceMonitor
- **Firmware type badge** on miner cards — color-coded pill (VNish=blue, Braiins=green, Stock=gray) derived from existing CGMiner firmware string; tooltip shows raw version
- **Thermal runaway detection** — alerts when any miner's chip temp rises ≥ 5°C within 60 seconds while above 70°C; fires tray popup + CRIT log event; auto-clears when temp stabilises; never changes any miner settings
- **ASIC hash instability detection** — alerts when current TH/s drops ≥ 20% below the miner's own rolling 10-minute average; fires tray popup + WARN log event; auto-clears when drop normalises
- Sidebar nav now has 7 tabs: Dashboard, Miners, Alerts, Firmware, Groups, Settings, Logs

---

## [2.0.0] — Initial Release (Refactor)

### Core
- `MinerData` dataclass with full ASIC metrics (hashrate, temps, fans, pools, chains)
- `CGMinerAPI` TCP client (port 4028) supporting multi-command fetch
- `parse_miner_data()` parser for VNish, Braiins OS, Stock BMMiner firmware
- Per-chain data: hashrate, chip temps, PCB temps, ASIC count, frequency, voltage, faults
- VNish miner state, fan PWM, total ASIC count detection
- Two-phase LAN scanner: quick-probe IP range → full-probe responding IPs (ThreadPoolExecutor)
- Auto-discover and add new miners found on network
- SQLite database (miners, readings, events tables)
- JSON config file on Desktop

### GUI
- Dark theme (GitHub-dark inspired, full QSS stylesheet)
- Sidebar navigation (icon-only, 64px wide)
- **Dashboard page** — responsive card grid per miner with hashrate, temp, fan, chain status
- **Miners page** — sortable table view with search, right-click context menu
- **Alerts page** — alert rules, thresholds, schedule, delivery settings
- **Settings page** — farm identity, network scan config, Gmail app password setup
- **Logs page** — event log with filter, clear, live updates
- Miner details dialog — hardware, chain status table, temperatures, fans, hashrate, pools
- Add miner dialog with test-connection button
- Network scan dialog with progress + multi-select
- Change pool dialog (single miner or all miners)
- System tray icon (minimize to tray, tray menu, popup alerts)
- Status chips (total TH/s, online/offline/warning counts)
- Auto-unlock VNish web UI in Chrome (color-detect gold button)

### Alerts
- Miner offline detection (configurable timeout)
- Low hashrate alerts (% below per-miner threshold)
- High/critical temperature alerts
- High HW error rate alerts
- Fan speed alerts
- Gmail SMTP delivery via app password (no OAuth needed)
- Multi-recipient email support
- Hourly / 12-hour / daily schedule
- Windows tray popup notifications
- HTML email with summary cards and issues table

### Build
- PyInstaller onefile build (`RigAlert.exe`)
- UPX compression, no console window
- Bundled assets: `rigalert.ico`, `rigalert_preview.png`
