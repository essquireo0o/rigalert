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
        """Fetch all miner data. Uses a single pipe connection when firmware supports it,
        falling back to sequential commands otherwise."""
        out: Dict[str, Any] = {}

        # Single connection for all 5 commands — CGMiner pipe syntax
        pipe = self._send("summary+devs+pools+stats+version")
        if pipe:
            # Standard format: uppercase top-level keys (BMMiner / stock CGMiner)
            if "SUMMARY" in pipe and pipe["SUMMARY"]:
                out["summary"] = pipe["SUMMARY"][0]
                if pipe.get("DEVS"):
                    out["devs"] = pipe["DEVS"]
                if pipe.get("POOLS"):
                    out["pools"] = pipe["POOLS"]
                if pipe.get("STATS"):
                    out["stats"] = pipe["STATS"]
                if pipe.get("VERSION") and pipe["VERSION"]:
                    out["version"] = pipe["VERSION"][0]
                return out

            # VNish pipe format: lowercase outer keys, each wrapping a mini-response
            # {"summary": [{"SUMMARY": [{data}], "STATUS": [...]}], "devs": [...], ...}
            if "summary" in pipe:
                for low, up, singular in [
                    ("summary", "SUMMARY", True),
                    ("devs",    "DEVS",    False),
                    ("pools",   "POOLS",   False),
                    ("stats",   "STATS",   False),
                    ("version", "VERSION", True),
                ]:
                    mini = pipe.get(low, [])
                    if isinstance(mini, list) and mini:
                        inner = mini[0]
                        if isinstance(inner, dict):
                            val = inner.get(up)
                            if val:
                                out[low] = val[0] if singular else val
                if "summary" in out:
                    return out

        # Fallback: sequential individual commands (older/non-standard firmware)
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

    def restart(self) -> tuple:
        """Send CGMiner 'restart' command. Returns (success, message)."""
        result = self._send("restart")
        if result is None:
            # CGMiner closes connection on restart — a None response can still mean success
            return True, "Restart command sent (connection closed by miner, as expected)"
        status = result.get("STATUS", [{}])
        code = status[0].get("STATUS", "").upper() if status else ""
        msg = status[0].get("Msg", "") if status else ""
        if code in ("S", "I"):
            return True, f"Restart OK: {msg}"
        return False, f"Restart response: {result}"

    def set_chain_enabled(self, chain_index: int, enabled: bool,
                          web_user: str = "root", web_password: str = "admin") -> tuple:
        """Enable or disable a hashboard by 0-based chain index.

        Tries CGMiner socket commands and VNISH HTTP REST API in parallel.
        Returns (success, message).
        """
        import threading as _threading

        value = "1" if enabled else "0"
        label = "enabled" if enabled else "disabled"
        results: Dict[str, Any] = {}

        # ── Socket commands (parallel) ─────────────────────────────
        def _send_asc():
            cmd = "ascenable" if enabled else "ascdisable"
            results["asc"] = self._send(cmd, str(chain_index))

        def _send_ascset():
            results["ascset"] = self._send("ascset", f"{chain_index},enable,{value}")

        def _send_ascset2():
            # VNISH alternate: ascset without numeric value
            action = "enable" if enabled else "disable"
            results["ascset2"] = self._send("ascset", f"{chain_index},{action}")

        t1 = _threading.Thread(target=_send_asc, daemon=True)
        t2 = _threading.Thread(target=_send_ascset, daemon=True)
        t3 = _threading.Thread(target=_send_ascset2, daemon=True)
        t1.start(); t2.start(); t3.start()
        t1.join(); t2.join(); t3.join()

        def _sock_ok(r) -> bool:
            if not r:
                return False
            s = r.get("STATUS", [{}])
            return (s[0].get("STATUS", "") if s else "").upper() in ("S", "I")

        for key in ("asc", "ascset", "ascset2"):
            if _sock_ok(results.get(key)):
                return True, f"Chain {chain_index + 1} {label} (socket)"

        # ── VNISH HTTP REST API ────────────────────────────────────
        ok, msg = self._http_set_chain_enabled(chain_index, enabled, web_user, web_password)
        if ok:
            return True, msg

        return False, f"Chain {chain_index + 1}: all commands rejected — check firmware permissions"

    def probe_api(self, web_user: str = "root", web_password: str = "admin") -> str:
        """Probe the miner HTTP API and return a diagnostic string."""
        import urllib.request, urllib.error, base64, threading as _t
        auth = "Basic " + base64.b64encode(f"{web_user}:{web_password}".encode()).decode()
        base = f"http://{self.host}"
        hdrs = {"Authorization": auth, "User-Agent": "RigAlert/1.0"}
        paths = [
            "/api/v1/config", "/api/v1/info", "/api/v1/summary",
            "/api/v1/stats", "/api/v1/mining", "/api/v1/miner/config",
            "/cgi-bin/get_miner_conf.cgi", "/cgi-bin/minerConfiguration.cgi",
        ]
        results = {}

        def _probe(path):
            try:
                req = urllib.request.Request(f"{base}{path}", headers=hdrs)
                with urllib.request.urlopen(req, timeout=3) as r:
                    body = r.read(600).decode("utf-8", errors="replace")
                    results[path] = f"HTTP {r.status}: {body[:400]}"
            except urllib.error.HTTPError as e:
                body = e.read(200).decode("utf-8", errors="replace")
                results[path] = f"HTTP {e.code}: {body[:200]}"
            except Exception as ex:
                results[path] = f"ERR: {ex}"

        threads = [_t.Thread(target=_probe, args=(p,), daemon=True) for p in paths]
        for t in threads: t.start()
        for t in threads: t.join()
        return "\n\n".join(f"GET {p}\n{results.get(p, 'no response')}" for p in paths)

    def _http_set_chain_enabled(self, chain_index: int, enabled: bool,
                                 user: str, password: str) -> tuple:
        import urllib.request, urllib.error, urllib.parse
        import base64, json as _json, threading as _t

        label = "enabled" if enabled else "disabled"
        auth  = "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()
        base  = f"http://{self.host}"
        jhdrs = {"Content-Type": "application/json",
                 "Authorization": auth, "User-Agent": "RigAlert/1.0"}
        fhdrs = {"Content-Type": "application/x-www-form-urlencoded",
                 "Authorization": auth, "User-Agent": "RigAlert/1.0"}
        winner: Dict[str, Any] = {}

        def _jcall(method, url, payload=None):
            try:
                req = urllib.request.Request(
                    url,
                    data=_json.dumps(payload).encode() if payload is not None else None,
                    method=method, headers=jhdrs,
                )
                with urllib.request.urlopen(req, timeout=3) as r:
                    return r.status, r.read(2000)
            except urllib.error.HTTPError as e:
                return e.code, e.read(200)
            except Exception:
                return None, b""

        def _fcall(url, form_dict):
            try:
                data = urllib.parse.urlencode(form_dict).encode()
                req = urllib.request.Request(url, data=data, method="POST", headers=fhdrs)
                with urllib.request.urlopen(req, timeout=3) as r:
                    return r.status, r.read(500)
            except urllib.error.HTTPError as e:
                return e.code, e.read(200)
            except Exception:
                return None, b""

        # ── LuCI login (get stok) ──────────────────────────────────
        stok = ""
        try:
            form = urllib.parse.urlencode(
                {"luci_username": user, "luci_password": password}
            ).encode()
            lr = urllib.request.Request(
                f"{base}/cgi-bin/luci/", data=form, method="POST",
                headers={"Content-Type": "application/x-www-form-urlencoded",
                         "User-Agent": "RigAlert/1.0"},
            )
            class _NR(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, *a, **k): return None
            opener = urllib.request.build_opener(_NR())
            try:
                with opener.open(lr, timeout=4) as r:
                    loc = r.headers.get("Location", "")
            except urllib.error.HTTPError as e:
                loc = e.headers.get("Location", "")
            if ";stok=" in loc:
                stok = loc.split(";stok=")[1].split("/")[0]
        except Exception:
            pass

        # ── Antminer CGI approach (read-modify-write) ──────────────
        def _try_antminer_cgi():
            if winner: return
            # Get current config
            s, body = _jcall("GET", f"{base}/cgi-bin/get_miner_conf.cgi")
            if s != 200: return
            try:
                cfg = _json.loads(body)
            except Exception:
                return
            # Antminer config uses "chain-X" keys or flat enabled flags
            val = "1" if enabled else "0"
            for key in (f"chain{chain_index}", f"chain-{chain_index}",
                        f"bitmain-chain{chain_index}"):
                if key in cfg:
                    cfg[key] = {"enabled": val} if isinstance(cfg[key], dict) else val
            # Also try top-level enabled flag
            for key in (f"chain{chain_index}-enabled",
                        f"chain{chain_index}_enabled"):
                if key in cfg:
                    cfg[key] = val
            # POST back
            s2, _ = _fcall(f"{base}/cgi-bin/set_miner_conf.cgi", cfg)
            if s2 in (200, 201, 204):
                winner["msg"] = f"Chain {chain_index+1} {label} (Antminer CGI)"

        # ── REST config read-modify-write (parallel per endpoint) ──
        api_roots = []
        if stok:
            api_roots.append(f"{base}/cgi-bin/luci/;stok={stok}")
        api_roots.append(base)

        def _try_rest_cfg(api_root, cfg_path):
            if winner: return
            s, body = _jcall("GET", f"{api_root}{cfg_path}")
            if s != 200: return
            try:
                cfg = _json.loads(body)
            except Exception:
                return
            modified = False
            for key in ("boards", "chains", "hashboards"):
                val = cfg.get(key)
                if isinstance(val, list):
                    for b in val:
                        for ik in ("index", "id", "board", "chain"):
                            if b.get(ik) == chain_index:
                                b["enabled"] = enabled
                                modified = True
                elif isinstance(val, dict):
                    k = str(chain_index)
                    if k in val:
                        entry = val[k]
                        if isinstance(entry, dict):
                            entry["enabled"] = enabled
                        else:
                            val[k] = {"enabled": enabled}
                        modified = True
            if not modified:
                return
            for method in ("POST", "PUT", "PATCH"):
                if winner: return
                s2, _ = _jcall(method, f"{api_root}{cfg_path}", cfg)
                if s2 in (200, 201, 204):
                    winner["msg"] = f"Chain {chain_index+1} {label}"
                    _jcall("POST", f"{base}/api/v1/restart", {})

        # ── Direct board endpoints (fire-and-forget style) ─────────
        direct = [
            ("POST", f"/api/v1/hashboard/{chain_index}", {"enabled": enabled}),
            ("PUT",  f"/api/v1/hashboard/{chain_index}", {"enabled": enabled}),
            ("POST", f"/api/v1/board/{chain_index}",     {"enabled": enabled}),
            ("POST", "/api/v1/hashboards", {"index": chain_index, "enabled": enabled}),
            ("POST", "/api/v1/chains",     {"index": chain_index, "enabled": enabled}),
            ("POST", "/api/v1/config",
             {"boards": [{"index": chain_index, "enabled": enabled}]}),
            ("POST", "/api/v1/config",
             {"chains": {str(chain_index): {"enabled": enabled}}}),
        ]

        def _try_direct(method, path, payload):
            if winner: return
            s, _ = _jcall(method, f"{base}{path}", payload)
            if s in (200, 201, 204):
                winner["msg"] = f"Chain {chain_index+1} {label}"
                _jcall("POST", f"{base}/api/v1/restart", {})

        # Launch all in parallel
        threads = [_t.Thread(target=_try_antminer_cgi, daemon=True)]
        for ar in api_roots:
            for cp in ("/api/v1/config", "/api/v1/mining/config",
                       "/api/v1/miner/config", "/api/v1/mining"):
                threads.append(_t.Thread(
                    target=_try_rest_cfg, args=(ar, cp), daemon=True))
        for method, path, payload in direct:
            threads.append(_t.Thread(
                target=_try_direct, args=(method, path, payload), daemon=True))

        for t in threads: t.start()
        for t in threads: t.join()

        if winner:
            return True, winner["msg"]
        return False, "HTTP: all endpoints rejected — click Probe API to diagnose"

    def locate(self, enabled: bool = True) -> tuple:
        """
        Best-effort miner identification through CGMiner-compatible commands.
        Different firmware exposes LED control under different privileged names.
        """
        value = "1" if enabled else "0"
        candidates = [
            ("ascset", f"0,led,{value}"),
            ("ascset", f"0,blink,{value}"),
            ("ascset", f"0,identify,{value}"),
            ("ascset", f"all,led,{value}"),
        ]
        for command, parameter in candidates:
            result = self._send(command, parameter)
            if not result:
                continue
            status = result.get("STATUS", [{}])
            code = status[0].get("STATUS", "").upper() if status else ""
            if code in ("S", "I"):
                return True, "Locate LED enabled" if enabled else "Locate LED disabled"
        return False, "Locate LED command was not accepted by this miner"


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
