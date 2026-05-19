import socket
import json
import logging
from typing import Optional, Dict, Any, List

from .miner import MinerData

logger = logging.getLogger(__name__)


def _sf(val, default=0.0) -> float:
    """Safe float — handles VNISH dash-separated sensor strings like '43-44-61-65' or '0-0'."""
    try:
        v = str(val).strip()
        # VNISH returns multi-sensor strings like '43-44-61-65' — take the highest value
        if "-" in v and not v.startswith("-"):
            parts = [p for p in v.split("-") if p.strip()]
            try:
                return max(float(p) for p in parts)
            except (ValueError, TypeError):
                pass
        return float(v)
    except (TypeError, ValueError):
        return default


def _si(val, default=0) -> int:
    try:
        return int(float(str(val).strip()))
    except (TypeError, ValueError):
        return default


def _mhs_to_ths(val) -> float:
    return _sf(val) / 1_000_000.0


def _ghs_to_ths(val) -> float:
    return _sf(val) / 1_000.0


def _ths(val) -> float:
    return _sf(val)


class CGMinerAPI:
    def __init__(self, host: str, port: int = 4028, timeout: float = 8.0):
        self.host = host
        self.port = port
        self.timeout = timeout

    def _send(self, command: str, parameter: str = "") -> Optional[Dict[str, Any]]:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(self.timeout)
                s.connect((self.host, self.port))
                if parameter:
                    cmd = json.dumps({"command": command, "parameter": parameter})
                else:
                    cmd = json.dumps({"command": command})
                s.sendall((cmd + "\n").encode("utf-8"))

                data = b""
                while True:
                    try:
                        chunk = s.recv(4096)
                    except socket.timeout:
                        break
                    if not chunk:
                        break
                    data += chunk
                    # Stop on null terminator (CGMiner protocol) or if response looks complete
                    if b"\x00" in data:
                        break

                data = data.replace(b"\x00", b"").strip()
                if data:
                    return json.loads(data.decode("utf-8", errors="replace"))
        except (socket.timeout, ConnectionRefusedError, TimeoutError, OSError) as e:
            logger.debug(f"[{self.host}] Connection error: {e}")
        except json.JSONDecodeError as e:
            logger.debug(f"[{self.host}] JSON error: {e}")
        return None

    def is_online(self) -> bool:
        return self._send("summary") is not None

    def fetch_all(self) -> Dict[str, Any]:
        """Fetch all miner data. Returns empty dict if miner is unreachable."""
        out: Dict[str, Any] = {}

        s = self._send("summary")
        if not s or "SUMMARY" not in s or not s["SUMMARY"]:
            return out
        out["summary"] = s["SUMMARY"][0]

        d = self._send("devs")
        if d and "DEVS" in d and d["DEVS"]:
            out["devs"] = d["DEVS"]

        p = self._send("pools")
        if p and "POOLS" in p:
            out["pools"] = p["POOLS"]

        st = self._send("stats")
        if st and "STATS" in st:
            out["stats"] = st["STATS"]

        v = self._send("version")
        if v and "VERSION" in v and v["VERSION"]:
            out["version"] = v["VERSION"][0]

        return out

    def quick_check(self) -> Optional[Dict[str, Any]]:
        """Quick single-connection check — just summary. Used during network scan."""
        s = self._send("summary")
        if s and "SUMMARY" in s and s["SUMMARY"]:
            return s["SUMMARY"][0]
        return None

    def change_pools(self, new_pools: List[Dict[str, str]]) -> tuple:
        """
        Replace miner pool config with new_pools list of {url, user, password}.
        Returns (success: bool, message: str).
        """
        # Count existing pools
        current_resp = self._send("pools")
        old_count = 0
        if current_resp and "POOLS" in current_resp:
            old_count = len(current_resp["POOLS"])

        # Add new pools
        added = 0
        for pool in new_pools:
            url = (pool.get("url") or "").strip()
            if not url:
                continue
            user = (pool.get("user") or "").strip()
            pwd  = (pool.get("password") or "x").strip() or "x"
            result = self._send("addpool", f"{url},{user},{pwd}")
            if result:
                added += 1

        if added == 0:
            return False, "No pools added — check URL format (stratum+tcp://host:port)"

        # Switch to first new pool (index = old_count)
        self._send("switchpool", str(old_count))

        # Remove old pools: always remove pool index 0 (indices shift down each time)
        for _ in range(old_count):
            self._send("removepool", "0")

        return True, f"{added} pool(s) set successfully"


def parse_miner_data(ip: str, port: int, raw: Dict[str, Any],
                     existing: Optional[MinerData] = None) -> MinerData:
    m = existing or MinerData(ip=ip, port=port)
    m.ip = ip
    m.port = port
    m.status = "online"

    summary = raw.get("summary", {})
    devs: List[Dict] = raw.get("devs", [])
    pools: List[Dict] = raw.get("pools", [])
    stats: List[Dict] = raw.get("stats", [])
    version = raw.get("version", {})

    # ── Uptime / shares ────────────────────────────────────────────────────
    if summary:
        m.uptime = _si(summary.get("Elapsed", 0))
        m.accepted = _si(summary.get("Accepted", 0))
        m.rejected = _si(summary.get("Rejected", 0))
        m.hw_errors = _si(summary.get("Hardware Errors", 0))
        m.hw_error_rate = _sf(summary.get("Device Hardware%", 0.0))

    # ── Hashrate ───────────────────────────────────────────────────────────
    # Priority: DEVS (per-board), then SUMMARY (aggregate)
    # Try all unit prefixes; VNISH uses GHS, standard uses MHS/THS

    def pick_hashrate(d: dict, suffixes=("5s", "1m", "5m", "15m", "av", "30m")):
        for suffix in suffixes:
            for prefix, fn in [("THS", _ths), ("GHS", _ghs_to_ths), ("MHS", _mhs_to_ths)]:
                key = f"{prefix} {suffix}"
                if key in d:
                    v = fn(d[key])
                    if v > 0:
                        return v, suffix
        return 0.0, ""

    # From DEVS (sum across boards)
    if devs:
        total_5s = total_1m = total_5m = total_av = 0.0
        for dev in devs:
            v, _ = pick_hashrate(dev, ("5s",))
            total_5s += v
            v, _ = pick_hashrate(dev, ("1m",))
            total_1m += v
            v, _ = pick_hashrate(dev, ("5m",))
            total_5m += v
            v, _ = pick_hashrate(dev, ("av",))
            total_av += v
        if total_5s > 0:
            m.hashrate_5s = total_5s
        if total_1m > 0:
            m.hashrate_1m = total_1m
        if total_5m > 0:
            m.hashrate_5m = total_5m
        # Use av as fallback for 5s if nothing else
        if m.hashrate_5s <= 0 and total_av > 0:
            m.hashrate_5s = total_av

    # From SUMMARY (fallback or override with better values)
    if summary:
        if m.hashrate_5s <= 0:
            v, _ = pick_hashrate(summary, ("5s", "av", "30m"))
            m.hashrate_5s = v
        if m.hashrate_1m <= 0:
            v, _ = pick_hashrate(summary, ("1m",))
            m.hashrate_1m = v
        if m.hashrate_5m <= 0:
            v, _ = pick_hashrate(summary, ("5m", "30m"))
            m.hashrate_5m = v
        if m.hashrate_15m <= 0:
            v, _ = pick_hashrate(summary, ("15m",))
            m.hashrate_15m = v

    # ── Temperature ────────────────────────────────────────────────────────
    board_temps = []
    chip_temps = []

    # From SUMMARY (some Braiins versions expose temp here)
    if summary:
        t = _sf(summary.get("Temperature", 0))
        if t > 5:
            board_temps.append(t)

    # From DEVS — Temperature = PCB/board; Chip Temp Max/Avg = chip (Braiins & stock S19+)
    for dev in devs:
        t = _sf(dev.get("Temperature", 0))
        if t > 5:
            board_temps.append(t)
        for chip_key in ("Chip Temp Max", "Chip Temp Avg", "Chip Temp"):
            ct = _sf(dev.get(chip_key, 0))
            if ct > 5:
                chip_temps.append(ct)
        # Inlet / outlet from DEVS (Braiins)
        for key, attr in [("Inlet Temp", "temp_inlet"), ("Outlet Temp", "temp_outlet")]:
            v = _sf(dev.get(key, 0))
            if v > 0:
                setattr(m, attr, v)

    # From STATS — handle Antminer/VNISH/Whatsminer formats
    for stat in stats:
        # Antminer: temp1/2/3 = board PCB, temp2_1/2_2/2_3 = chip, temp3_1/3_2/3_3 = chip2
        for i in range(1, 20):
            v = _sf(stat.get(f"temp{i}", -1))
            if v > 5:
                board_temps.append(v)
            for chip_prefix in ("temp2_", "temp3_"):
                v = _sf(stat.get(f"{chip_prefix}{i}", -1))
                if v > 5:
                    chip_temps.append(v)

        # Alternative key names
        for prefix, lst in [
            ("temp_pcb", board_temps), ("temp_chip", chip_temps),
            ("temp_board", board_temps), ("Chip Temp", chip_temps),
        ]:
            for i in range(1, 20):
                v = _sf(stat.get(f"{prefix}{i}", -1))
                if v > 5:
                    lst.append(v)

        # VNISH specific — sometimes uses "temp" fields differently
        for key in ["temp", "Temp", "Temperature"]:
            if key in stat:
                v = _sf(stat[key])
                if v > 5:
                    board_temps.append(v)

        # Inlet / outlet
        for key, attr in [
            ("temp_inlet", "temp_inlet"), ("Inlet Temp", "temp_inlet"),
            ("Inlet", "temp_inlet"),
            ("temp_outlet", "temp_outlet"), ("Outlet Temp", "temp_outlet"),
            ("Outlet", "temp_outlet"),
        ]:
            v = _sf(stat.get(key, 0))
            if v > 0:
                setattr(m, attr, v)

    if chip_temps:
        m.temp_chip_max = max(chip_temps)
        m.board_temps = board_temps
    elif board_temps:
        m.temp_chip_max = max(board_temps)
        m.board_temps = board_temps

    # ── Fan speed ──────────────────────────────────────────────────────────
    fan_speeds: List[int] = []
    fan_pcts: List[int] = []

    for stat in stats:
        for prefix in ("fan", "bitmain_fan", "Fan", "FAN"):
            for i in range(1, 12):
                v = _si(stat.get(f"{prefix}{i}", 0))
                if v > 0:
                    if v > 100:
                        fan_speeds.append(v)
                    else:
                        fan_pcts.append(v)
        # VNISH fan_speed field
        for key in ("fan_speed", "FanSpeed", "fan"):
            if key in stat:
                v = _si(stat[key])
                if v > 100:
                    fan_speeds.append(v)
                elif 0 < v <= 100:
                    fan_pcts.append(v)

    for dev in devs:
        for key in ("Fan Speed In", "Fan Speed Out", "Fan RPM", "Fan Speed",
                    "Inlet Fan Speed", "Outlet Fan Speed"):
            v = _si(dev.get(key, 0))
            if v > 100:
                fan_speeds.append(v)
        for key in ("Fan Percent", "Fan%", "Fan PWM"):
            v = _si(dev.get(key, 0))
            if 0 < v <= 100:
                fan_pcts.append(v)

    m.fan_speeds = list(dict.fromkeys(fan_speeds))
    m.fan_pcts = list(dict.fromkeys(fan_pcts))

    # ── Pool info ──────────────────────────────────────────────────────────
    if pools:
        alive = [p for p in pools if p.get("Status", "").lower() in ("alive", "active")]
        pool = sorted(alive or pools, key=lambda x: _si(x.get("Priority", 99)))[0]
        m.pool_url = str(pool.get("URL", ""))
        m.pool_user = str(pool.get("User", ""))
        m.pool_status = str(pool.get("Status", ""))

    # ── Firmware / model ───────────────────────────────────────────────────
    if version:
        # Braiins OS uses "BOSminer+" or "BOSminer" as the version key
        bos = version.get("BOSminer+", version.get("BOSminer", ""))
        if bos:
            m.firmware = f"Braiins OS {bos}"
        else:
            # Stock BMMiner / VNISH / generic CGMiner
            m.firmware = str(version.get("Miner", version.get("CGMiner", version.get("BMMiner", ""))))
        m.model = str(version.get("Type", ""))
        if not m.firmware:
            m.firmware = str(version.get("Description", ""))
        # Some firmware (older BMMiner) puts model in Description
        if not m.model:
            m.model = str(version.get("Description", ""))

    # ── All pools ──────────────────────────────────────────────────────────
    m.all_pools = [
        {
            "url": str(p.get("URL", "")),
            "user": str(p.get("User", "")),
            "status": str(p.get("Status", "")),
            "priority": _si(p.get("Priority", _si(p.get("POOL", 99)))),
            "accepted": _si(p.get("Accepted", 0)),
            "rejected": _si(p.get("Rejected", 0)),
            "diff": str(p.get("Diff", "")),
            "type": _si(p.get("Type", 0)),
        }
        for p in pools
        if str(p.get("URL", "")).lower() not in ("", "devfee") and _si(p.get("Type", 0)) == 0
    ]

    # ── VNISH: model from STATS[0], per-chain data from STATS[1] ──────────
    _vnish_meta: Dict[str, Any] = {}
    _vnish_metrics: Dict[str, Any] = {}
    for stat in stats:
        if "Type" in stat and ("Cgminer" in stat or ("Miner" in stat and "Elapsed" not in stat)):
            _vnish_meta = stat
        elif "chain_rate1" in stat or "fan_num" in stat or "total_acn" in stat:
            _vnish_metrics = stat

    if _vnish_meta:
        if not m.model:
            m.model = str(_vnish_meta.get("Type", ""))
        if not m.firmware:
            cgver = str(_vnish_meta.get("Cgminer", _vnish_meta.get("Miner", "")))
            compile_time = str(_vnish_meta.get("CompileTime", ""))
            m.firmware = (f"VNISH {cgver}  ({compile_time})" if cgver and compile_time
                          else f"VNISH {cgver}" if cgver else "")

    if _vnish_metrics:
        s = _vnish_metrics
        m.miner_state = str(s.get("state", ""))
        m.fan_pwm = _si(s.get("fan_pwm", 0))
        m.total_acn = _si(s.get("total_acn", 0))

        c_rates, c_ideals, c_chips, c_pcbs = [], [], [], []
        c_states, c_faults, c_acns, c_freqs, c_vols, c_cons = [], [], [], [], [], []

        for i in range(1, 10):
            rate_key = f"chain_rate{i}"
            if rate_key not in s and i > 3:
                break
            c_rates.append(_ghs_to_ths(s.get(f"chain_rate{i}", 0)))
            c_ideals.append(_ghs_to_ths(s.get(f"chain_rateideal{i}", 0)))
            c_chips.append(_sf(s.get(f"temp_chip{i}", 0)))
            c_pcbs.append(_sf(s.get(f"temp_pcb{i}", 0)))
            c_states.append(str(s.get(f"chain_state{i}", "")))
            c_faults.append(str(s.get(f"chain_fault{i}", "")))
            c_acns.append(_si(s.get(f"chain_acn{i}", 0)))
            c_freqs.append(_sf(s.get(f"freq_avg{i}", 0)))
            c_vols.append(_si(s.get(f"chain_vol{i}", 0)))
            c_cons.append(_si(s.get(f"chain_consumption{i}", 0)))

        m.chain_rates = c_rates
        m.chain_ideal_rates = c_ideals
        m.chain_temps_chip = c_chips
        m.chain_temps_pcb = c_pcbs
        m.chain_states = c_states
        m.chain_faults = c_faults
        m.chain_acns = c_acns
        m.chain_freqs = c_freqs
        m.chain_vols = c_vols
        m.chain_consumptions = c_cons

        # Use per-chain chip temps if they're better than what we found earlier
        valid_chips = [t for t in c_chips if t > 5]
        valid_pcbs = [t for t in c_pcbs if t > 5]
        if valid_chips and m.temp_chip_max <= 0:
            m.temp_chip_max = max(valid_chips)
            if not m.board_temps and valid_pcbs:
                m.board_temps = valid_pcbs

        # Use sum of chain rates as hashrate if summary gave us nothing
        chain_total = sum(c_rates)
        if chain_total > 0 and m.hashrate_5s <= 0:
            m.hashrate_5s = chain_total

        # Detect chain faults as alerts
        if m.has_chain_issues():
            for fault in m.chain_faults_summary():
                if fault not in m.alerts:
                    m.alerts.append(fault)

    return m
