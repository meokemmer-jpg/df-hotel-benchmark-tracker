"""Benchmark-Engine: Mock-KPI-Daten (RevPAR + Occupancy + ADR) [CRUX-MK]."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class HotelKPI:
    """Eine KPI-Snapshot fuer ein Hotel."""

    tenant_id: str
    name: str
    region: str
    adr: float  # Average Daily Rate in EUR
    occupancy: float  # [0, 1]

    @property
    def revpar(self) -> float:
        """Revenue per Available Room = ADR * Occupancy."""
        return self.adr * self.occupancy


class BenchmarkEngine:
    """Sammelt KPI-Snapshots ueber Hotels und liefert Aggregate."""

    def __init__(self) -> None:
        self._snapshots: dict[str, HotelKPI] = {}

    def add_snapshot(self, kpi: HotelKPI) -> None:
        if kpi.occupancy < 0 or kpi.occupancy > 1:
            raise ValueError("occupancy must be in [0, 1]")
        if kpi.adr < 0:
            raise ValueError("adr must be >= 0")
        self._snapshots[kpi.tenant_id] = kpi

    def all_snapshots(self) -> list[HotelKPI]:
        return list(self._snapshots.values())

    def get(self, tenant_id: str) -> HotelKPI | None:
        return self._snapshots.get(tenant_id)

    def values_for(self, kpi_name: str) -> list[float]:
        """Extract a KPI column over all hotels."""
        if kpi_name not in {"adr", "occupancy", "revpar"}:
            raise ValueError(f"unknown KPI: {kpi_name}")
        return [getattr(s, kpi_name) for s in self._snapshots.values()]

    def median(self, kpi_name: str) -> float:
        vals = sorted(self.values_for(kpi_name))
        n = len(vals)
        if n == 0:
            return 0.0
        if n % 2 == 1:
            return vals[n // 2]
        return (vals[n // 2 - 1] + vals[n // 2]) / 2.0

    def quantiles(self, kpi_name: str) -> tuple[float, float, float]:
        """Return (Q1, median, Q3) using inclusive linear interpolation."""
        vals = sorted(self.values_for(kpi_name))
        n = len(vals)
        if n == 0:
            return 0.0, 0.0, 0.0
        if n == 1:
            return vals[0], vals[0], vals[0]

        def _pct(p: float) -> float:
            pos = (n - 1) * p
            lo = int(pos)
            hi = min(lo + 1, n - 1)
            frac = pos - lo
            return vals[lo] + (vals[hi] - vals[lo]) * frac

        return _pct(0.25), _pct(0.5), _pct(0.75)


def load_mock_kpis() -> list[HotelKPI]:
    """Sandbox-Mock-Default: 5 Mock-Hotels, ein klarer Outlier (mock-5 mit ADR 410)."""
    return [
        HotelKPI(tenant_id="hildesheim", name="HeyLou Hildesheim", region="DE", adr=145.0, occupancy=0.78),
        HotelKPI(tenant_id="cape-coral", name="HeyLou Cape Coral", region="US", adr=189.0, occupancy=0.82),
        HotelKPI(tenant_id="munich", name="HeyLou Munich", region="DE", adr=220.0, occupancy=0.91),
        HotelKPI(tenant_id="mock-4", name="HeyLou Mock-4", region="DE", adr=130.0, occupancy=0.65),
        HotelKPI(tenant_id="mock-5", name="HeyLou Mock-5", region="AT", adr=410.0, occupancy=0.95),
    ]


def is_real_mode_enabled() -> bool:
    """Real-Mode-Gate via ENV-Var. Sandbox-Default ist mock."""
    flag = os.environ.get("DF_BENCHMARK_REAL_PMS_ENABLED", "").lower()
    return flag == "true"
