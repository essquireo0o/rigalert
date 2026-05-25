# RigAlert™ by ING Mining Commercial Product Roadmap

RigAlert is moving toward a commercial-grade ASIC miner monitoring and management product. The guiding rule is incremental improvement: build one feature at a time, test after each feature, update the changelog, and commit only once the app is stable.

## Product Guardrails

- Preserve existing working functionality.
- Keep changes modular and reversible.
- Maintain the dark RigAlert™ by ING Mining visual system.
- Never enable hashboards automatically.
- Never reboot, flash firmware, reset, or change pools without explicit user confirmation.
- Treat `192.168.1.223` as a VNish 1.2.7 read-only test miner unless explicit action is approved.
- Prefer read-only telemetry, dry runs, audit logging, and confirmation dialogs for management features.

## Phase 1 — Commercial Polish

- [x] Fix top header spacing/overflow and make the header look commercial.
- [ ] Make all pages visually consistent.
- [ ] Improve sidebar icons/tooltips.
- [ ] Add page titles and descriptions.
- [ ] Improve empty states.
- [ ] Improve table spacing and column sizing.
- [ ] Add loading states.
- [ ] Add toast notifications.
- [ ] Add confirmation dialogs.
- [ ] Add polished About page.
- [ ] Add version/build info.

## Phase 2 — Dashboard Upgrade

- [ ] Better fleet summary cards.
- [ ] Miner health score.
- [ ] Warning/offline/online breakdown.
- [ ] Revenue estimate card.
- [ ] BTC price card.
- [ ] Power cost card.
- [ ] Efficiency card.
- [ ] Mini charts for hashrate, temp, power.
- [ ] Click miner card to open detail page.

## Phase 3 — Miner Detail Page

- [ ] Full miner profile.
- [ ] Firmware type/version.
- [ ] Pool info.
- [ ] Hashboard status.
- [ ] Fan status.
- [ ] Temp history.
- [ ] Hashrate history.
- [ ] Error history.
- [ ] Notes.
- [ ] Maintenance status.
- [ ] Safe action buttons.

## Phase 4 — BTC / Altcoin Alerts

- [ ] Add coin watchlist.
- [ ] Support BTC, LTC, DOGE, BCH, KAS, ETC, XMR, ETH-style tracked assets where the selected API supports them.
- [ ] User sets above/below price alerts.
- [ ] User sets percent-move alerts.
- [ ] User sets daily/weekly movement alerts.
- [ ] Alert delivery through desktop, email, and Telegram.
- [ ] Alert history.
- [ ] Snooze/dismiss crypto alerts.
- [ ] Use CoinGecko or another no-key source first.

## Phase 5 — Alert Engine Cleanup

- [ ] Stop log spam from repeated low-hash warnings.
- [ ] Deduplicate repeated alerts.
- [ ] Add cooldown periods.
- [ ] Add alert severity levels.
- [ ] Add acknowledged/snoozed/resolved states.
- [ ] Add summary alert emails.
- [ ] Add per-miner thresholds.
- [ ] Add global default thresholds.

## Phase 6 — Firmware Tools

- [ ] VNish detection.
- [ ] Braiins OS detection.
- [ ] Stock Antminer detection.
- [ ] Firmware version display.
- [ ] Backup config button.
- [ ] Restore config button.
- [ ] Dry-run firmware install.
- [ ] Dry-run restore stock firmware.
- [ ] Explicit dangerous-action confirmation.
- [ ] Audit log every firmware action.

## Phase 7 — Miner Groups / Farm Layout

- [ ] Create/edit/delete groups.
- [ ] Site → Building → Row → Rack/Trough → Miner hierarchy.
- [ ] Drag miners into groups.
- [ ] Group dashboard.
- [ ] Group-level alerts.
- [ ] Group-level profitability.

## Phase 8 — Immersion Cooling

- [ ] Add immersion mode per miner/group.
- [ ] Fluid temp fields.
- [ ] Inlet/outlet temp fields.
- [ ] Pump status.
- [ ] Chiller status.
- [ ] Trough dashboard.
- [ ] PVC safety threshold.
- [ ] Cooling alerts.

## Phase 9 — Analytics / Reports

- [ ] Historical hashrate chart.
- [ ] Temperature chart.
- [ ] Power chart.
- [ ] Alert history chart.
- [ ] Export CSV.
- [ ] Export JSON.
- [ ] Daily summary report.
- [ ] Fleet uptime report.

## Phase 10 — Product Hardening

- [ ] Installer polish.
- [ ] App icon polish.
- [ ] Error handling.
- [ ] Settings validation.
- [ ] Secure credential storage.
- [ ] Backup/restore settings.
- [ ] Crash logging.
- [ ] Auto-update plan.
- [ ] License/about screen.
