# RigAlert™ Roadmap

## Status Legend
- ✅ Done  - 🔄 In Progress  - ⬜ Planned

---

## Phase 1 — Core Dashboard
- ✅ Miner card view (dashboard with live cards per miner)
- ✅ Miner table view (sortable, searchable)
- ✅ IP address, model, firmware, status, temperature, fan, hashrate, uptime, pool
- ✅ Status chips (total TH/s, online/offline/warning counts)
- ✅ System tray icon + minimize to tray

## Phase 2 — VNish & Multi-Firmware Integration
- ✅ VNish firmware detection (from CGMiner API)
- ✅ Per-chain data (hashrate, temperature, ASIC count, freq, voltage)
- ✅ Chain state badges (running/stopped/failure/disabled/auto-tuning)
- ✅ Braiins OS firmware detection
- ✅ Stock Antminer (BMMiner) firmware detection
- ✅ Disabled hashboard detection (shows chain state = disabled)
- 🔄 VNish HTTP REST API integration (read-only status, config)
- ⬜ Braiins OS HTTP/gRPC API integration

## Phase 3 — Firmware Tools
- ✅ Firmware type/version display per miner
- 🔄 Firmware tools page (dedicated UI)
- ⬜ Firmware config backup (VNish, Stock)
- ⬜ Firmware install wizard (dry-run → confirm → flash)
- ⬜ Firmware uninstall / restore stock workflow
- ⬜ VNish-specific controls (autotune, voltage, frequency)
- ⬜ Braiins OS-specific controls
- ⬜ Safety confirmation before any flash
- ⬜ Audit log for every firmware action

## Phase 4 — Alerts
- ✅ Miner offline alerts
- ✅ High temperature alerts (warn + critical)
- ✅ Low hashrate alerts (% below expected)
- ✅ High HW error rate alerts
- ✅ Fan speed alerts
- ✅ Email delivery (Gmail app password, multi-recipient)
- ✅ Windows tray popup alerts
- ✅ Hourly / 12-hour / daily alert schedule
- 🔄 Bitcoin price alerts (above/below thresholds)
- ⬜ Altcoin price alerts (configurable coins)
- ⬜ % price move alerts (e.g., BTC dropped 5% in 24h)
- ⬜ Push notifications (system)

## Phase 5 — GUI
- ✅ Dark theme (GitHub-dark inspired)
- ✅ Sidebar navigation
- ✅ Dashboard page (card grid)
- ✅ Miners page (table view)
- ✅ Alerts configuration page
- ✅ Settings page
- ✅ Logs page
- ✅ Miner details dialog (full hardware/chain/pool info)
- 🔄 Firmware tools page
- ⬜ Hashrate history charts per miner
- ⬜ Temperature history charts
- ⬜ Export CSV (readings, events)

## Phase 6 — Miner Management
- ✅ Add miner manually
- ✅ Remove miner
- ✅ Edit miner (name, min hashrate)
- ✅ LAN scan (auto-discover all miners on subnet)
- ✅ Change pool (single or all miners)
- ⬜ Miner groups / locations
- ⬜ Per-miner notes
- ⬜ Save/import miner list (CSV)

## Phase 7 — Monitoring & History
- ✅ Background polling (configurable interval)
- ✅ SQLite readings history (hashrate, temp, fan, shares)
- ✅ Event log (online/offline/warn events)
- ⬜ Hashrate trend charts
- ⬜ Temperature trend charts
- ⬜ Uptime history
- ⬜ Export readings to CSV

## Phase 8 — Safety Controls
- ✅ Read-only by default (never modifies miner config without user action)
- ✅ Confirmation dialog before pool changes
- ✅ SmartScreen note in readme (independent freeware)
- ⬜ Explicit read-only mode toggle
- ⬜ Test mode vs production mode
- ⬜ Full audit log for all write actions
- ⬜ Require IP confirmation before dangerous actions
