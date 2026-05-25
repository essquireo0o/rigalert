import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple

from PyQt6.QtCore import QThread, pyqtSignal

from .cgminer_api import CGMinerAPI, parse_miner_data
from .config import AppConfig
from .database import Database
from .firmware import detect_type
from .miner import MinerData

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScanTarget:
    ip: str
    port: int = 4028
    name: str = ""
    min_ths: float = 0.0


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
        if e < s:
            return []
        return [int_to_ip(i) for i in range(s, e + 1)]
    except Exception:
        return []


def _quick_probe_timed(ip: str, port: int, timeout: float) -> Tuple[bool, float, str]:
    """Single-command probe for discovery. It never mutates miner state."""
    started = time.perf_counter()
    try:
        api = CGMinerAPI(ip, port, timeout)
        return api.quick_check() is not None, time.perf_counter() - started, ""
    except Exception as exc:
        return False, time.perf_counter() - started, str(exc)


def _full_probe_timed(ip: str, port: int, timeout: float) -> Tuple[Optional[MinerData], float, str]:
    """Full read-only telemetry fetch. No reboot, pool, firmware, or hashboard commands."""
    started = time.perf_counter()
    try:
        api = CGMinerAPI(ip, port, timeout)
        raw = api.fetch_all()
        if not raw:
            return None, time.perf_counter() - started, "no response"
        miner = parse_miner_data(ip, port, raw)
        now = datetime.now()
        miner.last_seen = now
        miner.last_poll = now
        return miner, time.perf_counter() - started, ""
    except Exception as exc:
        return None, time.perf_counter() - started, str(exc)


class MinerScanner(QThread):
    miner_updated = pyqtSignal(object)       # MinerData
    miner_offline = pyqtSignal(str)          # ip
    scan_started = pyqtSignal()
    scan_finished = pyqtSignal(int)          # count found
    log_event = pyqtSignal(str, str, str)    # ip, level, message
    scan_progress = pyqtSignal(object)       # dict with phase/ip/count/elapsed
    scan_performance = pyqtSignal(object)    # dict with timing metrics

    def __init__(self, config: AppConfig, db: Database, parent=None):
        super().__init__(parent)
        self.config = config
        self.db = db
        self._running = False
        self._scan_requested = True
        self._full_scan_requested = True
        self._cancel_requested = False
        self._last_full_scan = 0.0
        self._miners: Dict[str, MinerData] = {}
        self._known_ips: List[ScanTarget] = []
        self._dead_until: Dict[str, float] = {}
        self._last_signatures: Dict[str, tuple] = {}

    def set_known_miners(self, miners: List[Dict]):
        self._known_ips = [
            ScanTarget(m["ip"], m.get("port", 4028), m.get("name", ""), m.get("min_ths", 0.0))
            for m in miners
        ]

    def add_miner(self, ip: str, port: int = 4028, name: str = "", min_ths: float = 0.0):
        self._known_ips = [e for e in self._known_ips if e.ip != ip]
        self._known_ips.append(ScanTarget(ip, port, name, min_ths))
        self.request_scan(full_network=False)

    def remove_miner(self, ip: str):
        self._known_ips = [e for e in self._known_ips if e.ip != ip]
        self._miners.pop(ip, None)
        self._last_signatures.pop(ip, None)

    def get_miner(self, ip: str) -> Optional[MinerData]:
        return self._miners.get(ip)

    def all_miners(self) -> List[MinerData]:
        return list(self._miners.values())

    def request_scan(self, full_network: bool = False):
        self._scan_requested = True
        if full_network:
            self._full_scan_requested = True
        self._cancel_requested = False

    def cancel_scan(self):
        self._cancel_requested = True
        self._scan_requested = False
        self.scan_progress.emit({
            "phase": "cancel",
            "message": "Cancelling scan...",
            "ip": "",
            "completed": 0,
            "total": 0,
            "found": len(self._miners),
            "elapsed": 0.0,
        })

    def stop(self):
        self._running = False
        self.cancel_scan()

    def run(self):
        self._running = True
        while self._running:
            auto_refresh = getattr(self.config, "auto_refresh_enabled", True)
            if self._scan_requested or auto_refresh:
                full_network = self._full_scan_requested or self._should_full_scan()
                self._scan_requested = False
                self._full_scan_requested = False
                self._cancel_requested = False
                self._do_scan(full_network=full_network)

            interval = max(1, int(getattr(self.config, "scan_interval_seconds", 60)))
            for _ in range(interval * 10):
                if not self._running or self._scan_requested:
                    break
                self.msleep(100)

    def _should_full_scan(self) -> bool:
        if not self._known_ips:
            return True
        minutes = max(0, int(getattr(self.config, "full_scan_interval_minutes", 15)))
        if minutes <= 0:
            return False
        return (time.time() - self._last_full_scan) >= minutes * 60

    def _do_scan(self, full_network: bool = False):
        started = time.perf_counter()
        cfg = self.config
        workers = max(1, min(512, int(getattr(cfg, "max_scan_workers", 50))))
        full_timeout = max(0.3, float(getattr(cfg, "connection_timeout", 8.0)))
        quick_timeout = max(0.15, min(full_timeout, float(getattr(cfg, "quick_scan_timeout", 0.8))))
        found = 0
        slow_count = 0
        known_targets = list(self._known_ips)
        known_ips = {t.ip for t in known_targets}

        self.scan_started.emit()
        self._emit_progress("known", "", 0, max(1, len(known_targets)), 0, started,
                            "Quick refresh: known miners first")

        known_found, known_slow = self._scan_full_targets(
            known_targets,
            timeout=full_timeout,
            workers=workers,
            started_at=started,
            phase="known",
            total_hint=max(1, len(known_targets)),
            newly_discovered=False,
        )
        found += known_found
        slow_count += known_slow

        discovered_targets: List[ScanTarget] = []
        discovery_checked = 0
        discovery_total = 0
        if full_network and not self._cancel_requested:
            self._last_full_scan = time.time()
            all_range = _ip_range(cfg.start_ip, cfg.end_ip)
            now = time.time()
            range_ips = [
                ip for ip in all_range
                if ip not in known_ips and self._dead_until.get(ip, 0) <= now
            ]
            discovery_total = len(range_ips)
            self._emit_progress("discover", "", 0, max(1, discovery_total), found, started,
                                "Full network discovery")
            responding, checked, quick_slow = self._scan_quick_targets(
                range_ips,
                cfg.miner_port,
                quick_timeout,
                workers,
                started,
                found,
            )
            discovery_checked = checked
            slow_count += quick_slow
            discovered_targets = [
                ScanTarget(ip, cfg.miner_port, "", cfg.default_min_ths)
                for ip in sorted(responding)
            ]

        if discovered_targets and not self._cancel_requested:
            new_found, new_slow = self._scan_full_targets(
                discovered_targets,
                timeout=full_timeout,
                workers=workers,
                started_at=started,
                phase="hydrate",
                total_hint=len(discovered_targets),
                newly_discovered=True,
            )
            found += new_found
            slow_count += new_slow

        elapsed = time.perf_counter() - started
        perf = {
            "mode": "full" if full_network else "quick",
            "found": found,
            "known_targets": len(known_targets),
            "discovery_checked": discovery_checked,
            "discovery_total": discovery_total,
            "new_targets": len(discovered_targets),
            "workers": workers,
            "quick_timeout": quick_timeout,
            "full_timeout": full_timeout,
            "slow_responses": slow_count,
            "cancelled": self._cancel_requested,
            "elapsed": elapsed,
        }
        logger.info(
            "Scan %s complete: found=%s known=%s discovery=%s/%s new=%s workers=%s elapsed=%.2fs slow=%s cancelled=%s",
            perf["mode"], found, len(known_targets), discovery_checked, discovery_total,
            len(discovered_targets), workers, elapsed, slow_count, self._cancel_requested,
        )
        self.scan_performance.emit(perf)
        self.scan_finished.emit(found)

    def _scan_full_targets(self, targets: List[ScanTarget], timeout: float, workers: int,
                           started_at: float, phase: str, total_hint: int,
                           newly_discovered: bool) -> Tuple[int, int]:
        if not targets:
            return 0, 0
        found = 0
        slow_count = 0
        slow_after = max(0.1, float(getattr(self.config, "slow_response_seconds", 2.5)))
        completed = 0
        pool = ThreadPoolExecutor(max_workers=min(workers, len(targets)))
        futures = {
            pool.submit(_full_probe_timed, t.ip, t.port, timeout): t
            for t in targets
        }
        try:
            for future in as_completed(futures):
                target = futures[future]
                if self._cancel_requested or not self._running:
                    pool.shutdown(wait=False, cancel_futures=True)
                    break

                completed += 1
                miner, elapsed, err = future.result()
                if elapsed >= slow_after:
                    slow_count += 1
                    logger.info("Slow miner response: %s full probe %.2fs (%s)", target.ip, elapsed, err or "ok")

                if miner is not None:
                    self._handle_miner_online(miner, target, newly_discovered)
                    found += 1
                else:
                    self._handle_miner_miss(target)

                self._emit_progress(phase, target.ip, completed, total_hint, found, started_at,
                                    f"{phase.title()} scan")
        finally:
            pool.shutdown(wait=not self._cancel_requested, cancel_futures=True)
        return found, slow_count

    def _scan_quick_targets(self, ips: List[str], port: int, timeout: float, workers: int,
                            started_at: float, found_so_far: int) -> Tuple[set, int, int]:
        responding = set()
        if not ips:
            return responding, 0, 0

        slow_count = 0
        completed = 0
        total = len(ips)
        slow_after = max(0.1, float(getattr(self.config, "slow_response_seconds", 2.5)))
        dead_backoff = max(0, int(getattr(self.config, "dead_host_backoff_seconds", 300)))
        pool = ThreadPoolExecutor(max_workers=min(workers, total))
        futures = {
            pool.submit(_quick_probe_timed, ip, port, timeout): ip
            for ip in ips
        }
        try:
            for future in as_completed(futures):
                ip = futures[future]
                if self._cancel_requested or not self._running:
                    pool.shutdown(wait=False, cancel_futures=True)
                    break

                completed += 1
                ok, elapsed, err = future.result()
                if ok:
                    responding.add(ip)
                elif dead_backoff:
                    self._dead_until[ip] = time.time() + dead_backoff
                if elapsed >= slow_after:
                    slow_count += 1
                    logger.info("Slow IP probe: %s quick probe %.2fs (%s)", ip, elapsed, err or "ok")

                self._emit_progress("discover", ip, completed, total, found_so_far + len(responding),
                                    started_at, "Full network discovery")
        finally:
            pool.shutdown(wait=not self._cancel_requested, cancel_futures=True)
        return responding, completed, slow_count

    def _handle_miner_online(self, miner: MinerData, target: ScanTarget, newly_discovered: bool):
        prev = self._miners.get(target.ip)
        if target.name:
            miner.name = target.name
        miner.hashrate_ideal = target.min_ths or self.config.default_min_ths
        self._check_alerts(miner, prev, self.config)
        self._miners[target.ip] = miner
        self.db.save_reading(miner)
        if newly_discovered:
            self.db.upsert_miner(target.ip, target.port, "", self.config.default_min_ths)
            if not any(t.ip == target.ip for t in self._known_ips):
                self._known_ips.append(target)

        firmware_type = detect_type(miner.firmware, miner.model)
        self.db.update_scan_cache(
            miner.ip,
            last_scan_at=datetime.now().isoformat(),
            firmware_type=firmware_type,
            firmware_fingerprint=(miner.firmware or miner.model or firmware_type),
            hostname=miner.display_name,
            vendor=firmware_type,
        )

        signature = self._miner_signature(miner)
        if self._last_signatures.get(miner.ip) != signature:
            self._last_signatures[miner.ip] = signature
            self.miner_updated.emit(miner)

    def _handle_miner_miss(self, target: ScanTarget):
        prev = self._miners.get(target.ip)
        if prev is not None and prev.last_seen:
            secs_since = (datetime.now() - prev.last_seen).total_seconds()
            if secs_since >= self.config.offline_after_seconds and prev.status != "offline":
                prev.status = "offline"
                self._miners[target.ip] = prev
                self.miner_offline.emit(target.ip)
                self.miner_updated.emit(prev)
                self.db.log_event(target.ip, "ERROR", f"Miner offline ({int(secs_since)}s since last contact)")
                self.log_event.emit(target.ip, "ERROR", "Miner went OFFLINE")

    def _miner_signature(self, m: MinerData) -> tuple:
        return (
            m.status,
            round(m.best_hashrate(), 3),
            round(m.temp_chip_max or m.temp_outlet or m.temp_inlet, 1),
            tuple(m.fan_speeds),
            tuple(m.fan_pcts),
            m.accepted,
            m.rejected,
            m.hw_errors,
            round(m.hw_error_rate, 3),
            m.pool_url,
            m.pool_status,
            m.uptime // 60,
            round(m.power_watts, 1),
            m.firmware,
            m.model,
            tuple(m.chain_states),
            tuple(m.chain_faults),
        )

    def _emit_progress(self, phase: str, ip: str, completed: int, total: int, found: int,
                       started_at: float, message: str):
        self.scan_progress.emit({
            "phase": phase,
            "ip": ip,
            "completed": completed,
            "total": total,
            "found": found,
            "elapsed": time.perf_counter() - started_at,
            "message": message,
        })

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
                alerts.append(f"Critical temp: {t:.0f}C")
            elif t >= cfg.warn_temp_c:
                alerts.append(f"High temp: {t:.0f}C")

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
                          max_workers: int = 100,
                          progress_callback: Optional[Callable[[dict], None]] = None,
                          cancel_callback: Optional[Callable[[], bool]] = None) -> List[MinerData]:
        """Dialog helper: discover a range and stream progress from a worker thread."""
        ips = _ip_range(start_ip, end_ip)
        quick_timeout = max(0.15, min(timeout, float(getattr(self.config, "quick_scan_timeout", 0.8))))
        responding = set()
        started = time.perf_counter()
        checked = 0

        def cancelled() -> bool:
            return bool(cancel_callback and cancel_callback())

        with ThreadPoolExecutor(max_workers=min(max_workers, len(ips) or 1)) as pool:
            futures = {pool.submit(_quick_probe_timed, ip, port, quick_timeout): ip for ip in ips}
            for future in as_completed(futures):
                if cancelled():
                    pool.shutdown(wait=False, cancel_futures=True)
                    break
                ip = futures[future]
                checked += 1
                ok, _, _ = future.result()
                if ok:
                    responding.add(ip)
                if progress_callback:
                    progress_callback({
                        "phase": "discover",
                        "ip": ip,
                        "completed": checked,
                        "total": len(ips),
                        "found": len(responding),
                        "elapsed": time.perf_counter() - started,
                    })

        found: List[MinerData] = []
        with ThreadPoolExecutor(max_workers=min(max_workers, len(responding) or 1)) as pool:
            futures = {pool.submit(_full_probe_timed, ip, port, timeout): ip for ip in responding}
            hydrated = 0
            for future in as_completed(futures):
                if cancelled():
                    pool.shutdown(wait=False, cancel_futures=True)
                    break
                ip = futures[future]
                hydrated += 1
                result, _, _ = future.result()
                if result is not None:
                    found.append(result)
                if progress_callback:
                    progress_callback({
                        "phase": "hydrate",
                        "ip": ip,
                        "completed": hydrated,
                        "total": len(responding),
                        "found": len(found),
                        "elapsed": time.perf_counter() - started,
                    })
        return found
