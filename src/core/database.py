import sqlite3
import os
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from .miner import MinerData
from .app_paths import get_app_dir

logger = logging.getLogger(__name__)

_DB_PATH = os.path.join(get_app_dir(), "rigalert.db")


class Database:
    def __init__(self, path: str = _DB_PATH):
        self.path = path
        self._init()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self):
        with self._conn() as c:
            c.executescript("""
                PRAGMA journal_mode=WAL;"""
            )
        with self._conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS miners (
                    ip TEXT PRIMARY KEY,
                    port INTEGER DEFAULT 4028,
                    name TEXT DEFAULT '',
                    min_ths REAL DEFAULT 0,
                    added_at TEXT,
                    notes TEXT DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip TEXT,
                    ts TEXT,
                    status TEXT,
                    hashrate REAL,
                    temp REAL,
                    fan_rpm INTEGER,
                    accepted INTEGER,
                    rejected INTEGER,
                    hw_errors INTEGER,
                    hw_err_pct REAL,
                    pool_url TEXT,
                    pool_status TEXT,
                    uptime INTEGER,
                    power_watts REAL
                );
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT,
                    ip TEXT,
                    level TEXT,
                    message TEXT
                );
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    color TEXT DEFAULT '#30363d',
                    notes TEXT DEFAULT ''
                );
                CREATE INDEX IF NOT EXISTS idx_readings_ip_ts ON readings(ip, ts);
                CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
            """)
        # Migrate existing databases that predate new columns
        for migration in [
            "ALTER TABLE miners ADD COLUMN notes TEXT DEFAULT ''",
            "ALTER TABLE miners ADD COLUMN group_id INTEGER DEFAULT NULL",
            "ALTER TABLE miners ADD COLUMN last_scan_at TEXT DEFAULT ''",
            "ALTER TABLE miners ADD COLUMN firmware_type TEXT DEFAULT ''",
            "ALTER TABLE miners ADD COLUMN firmware_fingerprint TEXT DEFAULT ''",
            "ALTER TABLE miners ADD COLUMN hostname TEXT DEFAULT ''",
            "ALTER TABLE miners ADD COLUMN vendor TEXT DEFAULT ''",
        ]:
            try:
                with self._conn() as c:
                    c.execute(migration)
            except sqlite3.OperationalError:
                pass  # Column already exists

    # ── Miners ────────────────────────────────────────────────────────────

    def upsert_miner(self, ip: str, port: int = 4028, name: str = "",
                     min_ths: float = 0.0, notes: str = "", group_id: int = None):
        with self._conn() as c:
            c.execute("""
                INSERT INTO miners(ip, port, name, min_ths, added_at, notes, group_id)
                VALUES(?,?,?,?,?,?,?)
                ON CONFLICT(ip) DO UPDATE SET
                    port=excluded.port,
                    name=excluded.name,
                    min_ths=excluded.min_ths,
                    notes=CASE WHEN excluded.notes != '' THEN excluded.notes ELSE notes END,
                    group_id=COALESCE(excluded.group_id, group_id)
            """, (ip, port, name, min_ths, datetime.now().isoformat(), notes, group_id))

    def update_notes(self, ip: str, notes: str):
        with self._conn() as c:
            c.execute("UPDATE miners SET notes=? WHERE ip=?", (notes, ip))

    def set_miner_group(self, ip: str, group_id: Optional[int]):
        with self._conn() as c:
            c.execute("UPDATE miners SET group_id=? WHERE ip=?", (group_id, ip))

    def update_scan_cache(self, ip: str, last_scan_at: str = "", firmware_type: str = "",
                          firmware_fingerprint: str = "", hostname: str = "",
                          vendor: str = ""):
        with self._conn() as c:
            c.execute("""
                UPDATE miners
                SET last_scan_at=?,
                    firmware_type=CASE WHEN ? != '' THEN ? ELSE firmware_type END,
                    firmware_fingerprint=CASE WHEN ? != '' THEN ? ELSE firmware_fingerprint END,
                    hostname=CASE WHEN ? != '' THEN ? ELSE hostname END,
                    vendor=CASE WHEN ? != '' THEN ? ELSE vendor END
                WHERE ip=?
            """, (
                last_scan_at,
                firmware_type, firmware_type,
                firmware_fingerprint, firmware_fingerprint,
                hostname, hostname,
                vendor, vendor,
                ip,
            ))

    # ── Groups ────────────────────────────────────────────────────────────

    def get_groups(self) -> List[Dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM groups ORDER BY name").fetchall()
            return [dict(r) for r in rows]

    def create_group(self, name: str, color: str = "#30363d", notes: str = "") -> int:
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO groups(name, color, notes) VALUES(?,?,?)", (name, color, notes)
            )
            return cur.lastrowid

    def update_group(self, group_id: int, name: str, color: str = "#30363d", notes: str = ""):
        with self._conn() as c:
            c.execute(
                "UPDATE groups SET name=?, color=?, notes=? WHERE id=?",
                (name, color, notes, group_id)
            )

    def delete_group(self, group_id: int):
        with self._conn() as c:
            c.execute("UPDATE miners SET group_id=NULL WHERE group_id=?", (group_id,))
            c.execute("DELETE FROM groups WHERE id=?", (group_id,))

    def delete_miner(self, ip: str):
        with self._conn() as c:
            c.execute("DELETE FROM miners WHERE ip=?", (ip,))

    def get_miners(self) -> List[Dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute("SELECT * FROM miners ORDER BY ip").fetchall()
            return [dict(r) for r in rows]

    # ── Readings ──────────────────────────────────────────────────────────

    def save_reading(self, m: MinerData):
        fan = m.fan_speeds[0] if m.fan_speeds else (m.fan_pcts[0] if m.fan_pcts else 0)
        with self._conn() as c:
            c.execute("""
                INSERT INTO readings(ip,ts,status,hashrate,temp,fan_rpm,accepted,rejected,
                    hw_errors,hw_err_pct,pool_url,pool_status,uptime,power_watts)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                m.ip,
                datetime.now().isoformat(),
                m.status,
                m.best_hashrate(),
                m.temp_chip_max or m.temp_outlet,
                fan,
                m.accepted,
                m.rejected,
                m.hw_errors,
                m.hw_error_rate,
                m.pool_url,
                m.pool_status,
                m.uptime,
                m.power_watts,
            ))

    def get_recent_readings(self, ip: str, limit: int = 100) -> List[Dict[str, Any]]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT * FROM readings WHERE ip=? ORDER BY ts DESC LIMIT ?",
                (ip, limit)
            ).fetchall()
            return [dict(r) for r in rows]

    def cleanup_old_readings(self, days: int = 30):
        cutoff = datetime.now().isoformat()[:10]
        # approximate: keep only readings within last N days
        with self._conn() as c:
            c.execute(
                "DELETE FROM readings WHERE ts < date('now', ?)",
                (f"-{days} days",)
            )

    # ── Events ────────────────────────────────────────────────────────────

    def log_event(self, ip: str, level: str, message: str):
        with self._conn() as c:
            c.execute(
                "INSERT INTO events(ts, ip, level, message) VALUES(?,?,?,?)",
                (datetime.now().isoformat(), ip, level, message)
            )
        logger.info(f"[{ip}] {level}: {message}")

    def get_events(self, limit: int = 500, ip: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._conn() as c:
            if ip:
                rows = c.execute(
                    "SELECT * FROM events WHERE ip=? ORDER BY ts DESC LIMIT ?",
                    (ip, limit)
                ).fetchall()
            else:
                rows = c.execute(
                    "SELECT * FROM events ORDER BY ts DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            return [dict(r) for r in rows]

    def clear_events(self):
        with self._conn() as c:
            c.execute("DELETE FROM events")
