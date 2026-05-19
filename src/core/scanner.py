import logging
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional

from PyQt6.QtCore import QThread, pyqtSignal

from .cgminer_api import CGMinerAPI, parse_miner_data
from .config import AppConfig
from .database import Database
from .miner import MinerData

logger = logging.getLogger(__name__)


def _ip_range(start: str, end: str) -> List[str]:
    def ip_to_int(ip):
        parts = ip.strip().split(".")
        val = 0
        for p in parts:
            val = val * 256 + int(p)
        return val

    def int_to_ip(n):
        return ".".join(str((n >> (24 - i * 8)) & 0xFF) for i in range(4))

    try:
        s = ip_to_int(start)
        e = ip_to_int(end)
        return [int_to_ip(i) for i in range(s, e + 1)]
    except Exception:
        return []


def _quick_probe(ip: str, port: int, timeout: float) -> bool:
    """Fast check: single connection, just summary. Used for IP range scanning."""
    api = CGMinerAPI(ip, port, min(timeout, 4.0))
    return api.quick_check() is not None


def _full_probe(ip: str, port: int, timeout: float) -> Optional[MinerData]:
    """Full fetch: all commands. Used for known/discovered miners."""
    api = CGMinerAPI(ip, port, timeout)
    raw = api.fetch_all()
    if not raw:
        return None
    m = parse_miner_data(ip, port, raw)
    m.last_seen = datetime.now()
    m.last_poll = datetime.now()
    return m


class MinerScanner(QThread):
    miner_updated = pyqtSignal(object)       # MinerData
    miner_offline = pyqtSignal(str)          # ip
    scan_started = pyqtSignal()
    scan_finished = pyqtSignal(int)          # count found
    log_event = pyqtSignal(str, str, str)    # ip, level, message

    def __init__(self, config: AppConfig, db: Database, parent=None):
        super().__init__(parent)
        self.config = config
        self.db = db
        self._running = False
        self._miners: Dict[str, MinerData] = {}
        self._known_ips: List[str] = []

    def set_known_miners(self, miners: List[Dict]):
        self._known_ips = [(m["ip"], m.get("port", 4028), m.get("name", ""), m.get("min_ths", 0.0))
                           for m in miners]

    def add_miner(self, ip: str, port: int = 4028, name: str = "", min_ths: float = 0.0):
        entry = (ip, port, name, min_ths)
        if entry not in self._known_ips:
            self._known_ips = [e for e in self._known_ips if e[0] != ip]
            self._known_ips.append(entry)

    def remove_miner(self, ip: str):
        self._known_ips = [e for e in self._known_ips if e[0] != ip]
        self._miners.pop(ip, None)

    def get_miner(self, ip: str) -> Optional[MinerData]:
        return self._miners.get(ip)

    def all_miners(self) -> List[MinerData]:
        return list(self._miners.values())

    def stop(self):
        self._running = False

    def run(self):
        self._running = True
        while self._running:
            self._do_scan()
            # Sleep in small chunks so stop() is responsive
            for _ in range(self.config.scan_interval_seconds * 10):
                if not self._running:
                    break
                self.msleep(100)

    def _do_scan(self):
        self.scan_started.emit()
        cfg = self.config
        found = 0

        known_set = {t[0] for t in self._known_ips}

        # ── Phase 1: Quick-probe the full IP range (1 connection per IP) ──────
        range_ips = [ip for ip in _ip_range(cfg.start_ip, cfg.end_ip)
                     if ip not in known_set]

        newly_discovered = set()
        with ThreadPoolExecutor(max_workers=cfg.max_scan_workers) as pool:
            future_map = {
                pool.submit(_quick_probe, ip, cfg.miner_port, cfg.connection_timeout): ip
                for ip in range_ips
            }
            for future in as_completed(future_map):
                if not self._running:
                    break
                ip = future_map[future]
                try:
                    if future.result():
                        newly_discovered.add(ip)
                except Exception:
                    pass

        # ── Phase 2: Full-probe known miners + newly discovered ───────────────
        full_targets = list(self._known_ips)
        for ip in newly_discovered:
            full_targets.append((ip, cfg.miner_port, "", cfg.default_min_ths))

        with ThreadPoolExecutor(max_workers=min(cfg.max_scan_workers, len(full_targets) or 1)) as pool:
            future_map = {
                pool.submit(_full_probe, ip, port, cfg.connection_timeout): (ip, port, name, min_ths)
                for ip, port, name, min_ths in full_targets
            }
            for future in as_completed(future_map):
                if not self._running:
                    break
                ip, port, name, min_ths = future_map[future]
                try:
                    result = future.result()
                except Exception as e:
                    result = None
                    logger.debug(f"[{ip}] probe error: {e}")

                prev = self._miners.get(ip)

                if result is not None:
                    if name:
                        result.name = name
                    result.hashrate_ideal = min_ths or cfg.default_min_ths
                    self._check_alerts(result, prev, cfg)
                    self._miners[ip] = result
                    self.db.save_reading(result)
                    if ip in newly_discovered:
                        self.db.upsert_miner(ip, port, "", cfg.default_min_ths)
                        entry = (ip, port, "", cfg.default_min_ths)
                        if entry not in self._known_ips:
                            self._known_ips.append(entry)
                    self.miner_updated.emit(result)
                    found += 1
                else:
                    if prev is not None and prev.last_seen:
                        secs_since = (datetime.now() - prev.last_seen).total_seconds()
                        if secs_since >= cfg.offline_after_seconds and prev.status != "offline":
                            prev.status = "offline"
                            self._miners[ip] = prev
                            self.miner_offline.emit(ip)
                            self.miner_updated.emit(prev)
                            self.db.log_event(ip, "ERROR", f"Miner offline ({int(secs_since)}s since last contact)")
                            self.log_event.emit(ip, "ERROR", "Miner went OFFLINE")

        self.scan_finished.emit(found)

    def _check_alerts(self, m: MinerData, prev: Optional[MinerData], cfg: AppConfig):
        alerts = []

        if prev and prev.status == "offline":
            msg = f"{m.display_name} is back ONLINE"
            self.db.log_event(m.ip, "INFO", msg)
            self.log_event.emit(m.ip, "INFO", msg)

        if cfg.alert_low_hash_enabled and m.hashrate_ideal > 0:
            hs = m.best_hashrate()
            if hs < m.hashrate_ideal * 0.9:
                alerts.append(f"Low hashrate: {m.display_hashrate()} (expected {m.hashrate_ideal:.0f} TH/s)")

        if cfg.alert_temp_enabled:
            t = m.temp_chip_max or m.temp_outlet
            if t >= cfg.high_temp_c:
                alerts.append(f"Critical temp: {t:.0f}°C")
            elif t >= cfg.warn_temp_c:
                alerts.append(f"High temp: {t:.0f}°C")

        if cfg.alert_hw_err_enabled and m.hw_error_rate >= cfg.max_hw_error_rate:
            alerts.append(f"High HW error rate: {m.hw_error_rate:.2f}%")

        if cfg.alert_fan_enabled and cfg.min_fan_rpm > 0 and m.fan_speeds:
            low_fans = [f for f in m.fan_speeds if 0 < f < cfg.min_fan_rpm]
            if low_fans:
                alerts.append(f"Low fan speed: {min(low_fans)} RPM")

        m.alerts = alerts
        if alerts:
            m.status = "warning"
            for a in alerts:
                self.db.log_event(m.ip, "WARN", a)
                self.log_event.emit(m.ip, "WARN", a)


    def scan_network_once(self, start_ip: str, end_ip: str, port: int, timeout: float,
                          max_workers: int = 100) -> List[MinerData]:
        """Quick-probe every IP, then full-probe the ones that respond."""
        ips = _ip_range(start_ip, end_ip)
        responding = set()
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(_quick_probe, ip, port, timeout): ip for ip in ips}
            for future in as_completed(futures):
                ip = futures[future]
                try:
                    if future.result():
                        responding.add(ip)
                except Exception:
                    pass

        found = []
        with ThreadPoolExecutor(max_workers=min(max_workers, len(responding) or 1)) as pool:
            futures = {pool.submit(_full_probe, ip, port, timeout): ip for ip in responding}
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result is not None:
                        found.append(result)
                except Exception:
                    pass
        return found
