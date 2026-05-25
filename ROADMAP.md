# RigAlert™ by ING Mining — Product Roadmap

## Status Legend
- ✅ Done  - 🔄 In Progress  - ⬜ Planned  - 🔒 Blocked

---

## PHASE 1 — FOUNDATION ✅ (complete)
1. ✅ Professional RigAlert™ dashboard (card view + table view)
2. ✅ Sidebar navigation (icon-based, 6 tabs)
3. ✅ Miner card system (per-miner cards with live data)
4. ✅ Settings page
5. ✅ Logs page
6. ✅ Dark industrial UI (GitHub-dark inspired, gold/green/red accents)
7. ✅ Responsive card layout
8. ✅ Status indicators (online/offline/warning/critical)
9. ✅ Live refresh engine (background QThread scanner)
10. ✅ Persistent configuration (JSON config + SQLite DB)

---

## PHASE 2 — MINER MANAGEMENT 🔄
1. ✅ Add miner manually
2. ✅ Edit miner (name, min hashrate, notes)
3. ✅ Remove miner
4. ✅ LAN scanner (auto-discover subnet)
5. ⬜ Bulk miner import (CSV)
6. 🔄 Miner groups (flat + hierarchical)
7. ⬜ Farm hierarchy: Site → Building → Row → Rack/Trough → Miner
8. ✅ Miner tags and notes
9. ✅ Online/offline detection
10. ✅ Read-only monitoring mode (never modifies without explicit action)

---

## PHASE 3 — FIRMWARE SYSTEM 🔄
1. ✅ Detect VNish firmware
2. ✅ Detect Braiins OS firmware
3. ✅ Detect stock Antminer firmware
4. ✅ Firmware version detection (from CGMiner API)
5. 🔄 Firmware config backup (VNish HTTP API)
6. ⬜ Firmware restore workflow
7. ⬜ Firmware install wizard (file upload)
8. ⬜ Firmware uninstall workflow
9. ✅ Dry-run mode (all dangerous actions simulate before executing)
10. ✅ Dangerous action confirmation dialogs
11. 🔄 Firmware audit logging
12. ⬜ Firmware compatibility checker (model × firmware matrix)
13. ⬜ Recovery mode support

---

## PHASE 4 — ASIC TELEMETRY 🔄
1. ✅ Hashrate monitoring (5s, 1m, 5m, 15m)
2. ✅ Wattage monitoring (where reported by firmware)
3. ✅ ASIC chip temps (chip max, PCB, inlet, outlet)
4. ✅ Fan RPM monitoring
5. ✅ Pool monitoring (URL, user, status, accepted/rejected)
6. ✅ Uptime monitoring
7. ✅ Chain/hashboard detection + per-chain data (VNish)
8. ✅ HW error detection
9. ✅ Rejected share monitoring
10. ⬜ Autotune status monitoring
11. ⬜ ASIC instability detection
12. ⬜ Thermal runaway detection
13. ✅ Historical telemetry storage (SQLite readings table)

---

## PHASE 5 — IMMERSION COOLING ⬜
1. ⬜ Immersion mode toggle per miner
2. ⬜ Fluid temperature monitoring
3. ⬜ Inlet/outlet temperature tracking
4. ⬜ Pump monitoring
5. ⬜ Chiller monitoring
6. ⬜ Trough management (assign miners to troughs)
7. ⬜ Flow-rate monitoring
8. ⬜ Emergency thermal shutdown protocol
9. ⬜ PVC temperature safety thresholds
10. ⬜ Immersion cooling dashboard
11. ⬜ Cooling analytics

---

## PHASE 6 — ALERT SYSTEM 🔄
1. ✅ Miner offline alerts
2. ✅ High temperature alerts (warn + critical)
3. ✅ Low hashrate alerts
4. ✅ Pool disconnect detection
5. ✅ Fan failure alerts
6. ⬜ Firmware change alerts
7. ⬜ Thermal runaway alerts
8. ⬜ Immersion cooling alerts
9. ⬜ Telegram alerts
10. ⬜ Discord alerts
11. ✅ Email alerts (Gmail app password)
12. ✅ Desktop tray notifications
13. ⬜ Alert acknowledgement system
14. ⬜ Alert escalation logic (warn → critical → notify)

---

## PHASE 7 — MARKET / CRYPTO ✅ (basic)
1. ✅ Bitcoin price alerts (above/below threshold)
2. ✅ Altcoin price alerts (CoinGecko, any coin ID)
3. ✅ User-defined thresholds
4. ✅ Percentage move alerts (24h ±%)
5. ⬜ Profitability calculator
6. ⬜ Power cost calculator
7. ⬜ Fleet efficiency rankings
8. ⬜ Estimated revenue display
9. ⬜ Coin watchlist
10. ⬜ Mining calculator dashboard

---

## PHASE 8 — ANALYTICS ⬜
1. ⬜ Historical hashrate charts (per miner + fleet)
2. ⬜ Temperature history charts
3. ⬜ Power history charts
4. ⬜ Pool history
5. ⬜ Uptime analytics
6. ⬜ Fleet analytics (aggregate trends)
7. ⬜ Export CSV (readings, events)
8. ⬜ Export JSON
9. ⬜ Reporting engine

---

## PHASE 9 — ADVANCED OPERATIONS ⬜
1. ⬜ Batch operations (apply action to selected miners)
2. ⬜ Safe reboot workflow (with confirmation + audit log)
3. ⬜ Profile system (save/load miner configs)
4. ⬜ Tuning presets (undervolting, performance, efficiency)
5. ⬜ Undervolt presets
6. ⬜ Immersion cooling presets
7. ⬜ Scheduled maintenance windows
8. ⬜ Maintenance mode (suppress alerts while working)
9. ✅ Test/dry-run mode
10. 🔄 Full audit log (all write actions)
11. ⬜ Operator permissions/roles
12. ⬜ Operator accounts

---

## PHASE 10 — FUTURE ⬜
1. ⬜ Mobile companion app
2. ⬜ Web dashboard
3. ⬜ Multi-user support
4. ⬜ Cloud sync
5. ⬜ Remote access gateway
6. ⬜ AI diagnostics
7. ⬜ Predictive failure detection
8. ⬜ Smart autotuning recommendations
9. ⬜ ASIC health scoring
10. ⬜ Self-healing automation
