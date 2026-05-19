from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class MinerData:
    ip: str
    port: int = 4028
    name: str = ""
    miner_type: str = "ASIC"

    status: str = "unknown"  # online, offline, warning, error, unknown
    last_seen: Optional[datetime] = None
    last_poll: Optional[datetime] = None
    uptime: int = 0  # seconds

    hashrate_5s: float = 0.0   # TH/s
    hashrate_1m: float = 0.0
    hashrate_5m: float = 0.0
    hashrate_15m: float = 0.0
    hashrate_ideal: float = 0.0

    temp_inlet: float = 0.0
    temp_outlet: float = 0.0
    temp_chip_max: float = 0.0
    board_temps: List[float] = field(default_factory=list)

    fan_speeds: List[int] = field(default_factory=list)
    fan_pcts: List[int] = field(default_factory=list)
    fan_pwm: int = 0

    accepted: int = 0
    rejected: int = 0
    hw_errors: int = 0
    hw_error_rate: float = 0.0

    pool_url: str = ""
    pool_user: str = ""
    pool_status: str = ""
    all_pools: List[dict] = field(default_factory=list)

    alerts: List[str] = field(default_factory=list)

    power_watts: float = 0.0
    efficiency: float = 0.0

    firmware: str = ""
    model: str = ""

    # VNISH / per-chain data
    miner_state: str = ""
    total_acn: int = 0           # total ASIC chip count
    chain_rates: List[float] = field(default_factory=list)         # TH/s per chain
    chain_ideal_rates: List[float] = field(default_factory=list)   # TH/s ideal per chain
    chain_temps_chip: List[float] = field(default_factory=list)    # chip °C per chain
    chain_temps_pcb: List[float] = field(default_factory=list)     # PCB °C per chain
    chain_states: List[str] = field(default_factory=list)          # state per chain
    chain_faults: List[str] = field(default_factory=list)          # fault string per chain
    chain_acns: List[int] = field(default_factory=list)            # ASIC count per chain
    chain_freqs: List[float] = field(default_factory=list)         # MHz per chain
    chain_vols: List[int] = field(default_factory=list)            # mV per chain
    chain_consumptions: List[int] = field(default_factory=list)    # W per chain

    def best_hashrate(self) -> float:
        return self.hashrate_5m or self.hashrate_1m or self.hashrate_5s

    def display_hashrate(self) -> str:
        hs = self.best_hashrate()
        if hs <= 0:
            return "0 TH/s"
        if hs >= 1000:
            return f"{hs/1000:.2f} PH/s"
        if hs >= 1:
            return f"{hs:.2f} TH/s"
        if hs >= 0.001:
            return f"{hs*1000:.1f} GH/s"
        return f"{hs*1e6:.0f} MH/s"

    def display_temp(self) -> str:
        t = self.temp_chip_max or self.temp_outlet or self.temp_inlet
        if t > 0:
            return f"{t:.0f}°C"
        return "N/A"

    def display_fan(self) -> str:
        if self.fan_speeds:
            avg = sum(self.fan_speeds) / len(self.fan_speeds)
            return f"{avg:,.0f} RPM"
        if self.fan_pcts:
            avg = sum(self.fan_pcts) / len(self.fan_pcts)
            return f"{avg:.0f}%"
        return "N/A"

    def display_uptime(self) -> str:
        s = self.uptime
        if s <= 0:
            return "N/A"
        d, rem = divmod(s, 86400)
        h, rem = divmod(rem, 3600)
        m = rem // 60
        if d > 0:
            return f"{d}d {h}h"
        if h > 0:
            return f"{h}h {m}m"
        return f"{m}m"

    def temp_level(self, warn_c: float = 75.0, crit_c: float = 85.0) -> str:
        t = self.temp_chip_max or self.temp_outlet
        if t <= 0:
            return "unknown"
        if t >= crit_c:
            return "critical"
        if t >= warn_c:
            return "warning"
        return "ok"

    def hashrate_pct(self) -> float:
        if self.hashrate_ideal <= 0:
            return 100.0
        return min(100.0, (self.best_hashrate() / self.hashrate_ideal) * 100.0)

    def has_chain_issues(self) -> bool:
        return any(s in ("failure", "dead") for s in self.chain_states)

    def chain_faults_summary(self) -> List[str]:
        return [f"Ch{i+1}: {fault}" for i, fault in enumerate(self.chain_faults) if fault.strip()]

    @property
    def display_name(self) -> str:
        return self.name if self.name else self.ip

    def to_dict(self) -> dict:
        return {
            "ip": self.ip,
            "port": self.port,
            "name": self.name,
            "miner_type": self.miner_type,
            "status": self.status,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "hashrate_5m": self.hashrate_5m,
            "hashrate_1m": self.hashrate_1m,
            "hashrate_5s": self.hashrate_5s,
            "hashrate_ideal": self.hashrate_ideal,
            "temp_chip_max": self.temp_chip_max,
            "temp_outlet": self.temp_outlet,
            "temp_inlet": self.temp_inlet,
            "board_temps": self.board_temps,
            "fan_speeds": self.fan_speeds,
            "fan_pcts": self.fan_pcts,
            "accepted": self.accepted,
            "rejected": self.rejected,
            "hw_errors": self.hw_errors,
            "hw_error_rate": self.hw_error_rate,
            "pool_url": self.pool_url,
            "pool_user": self.pool_user,
            "pool_status": self.pool_status,
            "uptime": self.uptime,
            "power_watts": self.power_watts,
            "firmware": self.firmware,
            "model": self.model,
            "alerts": self.alerts,
            "miner_state": self.miner_state,
            "chain_states": self.chain_states,
        }
