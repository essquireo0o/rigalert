# Changelog

All notable changes to RigAlert™ are documented here.

---

## [Unreleased]

### Added
- ROADMAP.md and CHANGELOG.md

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
