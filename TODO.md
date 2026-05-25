# RigAlert™ — TODO (Current Sprint)

## Immediate Next Features

### Header & Dashboard
- [ ] Add BTC price chip to top status bar (live from PriceMonitor)
- [ ] Add fleet power (W) and efficiency (W/TH) to status bar
- [ ] Fleet summary stats section in Dashboard page
- [ ] Enhanced miner card with firmware badge

### Miner Management
- [x] Per-miner notes field (done)
- [ ] Miner groups — flat group system (simple tags/labels)
- [ ] Group filter in Miners table view
- [ ] Farm hierarchy DB schema (Site → Building → Row → Rack)
- [ ] Bulk import from CSV

### Monitoring & Alerts
- [ ] Historical hashrate chart per miner (mini sparkline in card)
- [ ] Thermal runaway detection (temp rising rapidly)
- [ ] ASIC instability detection (frequent hash drops)
- [ ] Telegram alert integration
- [ ] Alert acknowledgement (dismiss + snooze)

### Firmware
- [ ] VNish HTTP API for accurate firmware version
- [ ] Braiins OS detection via HTTP (port 8080)
- [ ] Firmware compatibility matrix
- [ ] Actual firmware backup download (VNish JSON config)

### Analytics
- [ ] Hashrate history chart (past 24h per miner)
- [ ] Temperature history chart
- [ ] Export readings to CSV
- [ ] Fleet efficiency dashboard panel

### Audit & Safety
- [ ] Proper audit log page (separate from event logs)
- [ ] All write actions logged with timestamp + operator
- [ ] Safe reboot workflow with countdown + cancel

## Backlog

- Immersion cooling dashboard
- Pool bulk change with rollback
- Telegram/Discord integration
- Profitability calculator
- Power cost calculator
- Mobile companion app
- Web dashboard
