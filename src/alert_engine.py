"""Alert-Engine: Outlier-Detection mit 1.5x-IQR-Rule [CRUX-MK]."""

from __future__ import annotations

from dataclasses import dataclass

from .benchmark_engine import BenchmarkEngine


@dataclass(frozen=True)
class Alert:
    """Ein Outlier-Alert."""

    tenant_id: str
    kpi_name: str
    value: float
    median: float
    q1: float
    q3: float
    iqr: float
    severity: str  # "LOW" | "HIGH"
    direction: str  # "above" | "below"


class IQROutlierDetector:
    """1.5x-IQR-Rule fuer Outlier-Detection mit konfigurierbarem Multiplier."""

    def __init__(self, outlier_multiplier: float = 1.5, severe_multiplier: float = 3.0) -> None:
        if outlier_multiplier <= 0:
            raise ValueError("outlier_multiplier must be > 0")
        if severe_multiplier <= outlier_multiplier:
            raise ValueError("severe_multiplier must be > outlier_multiplier")
        self.outlier_multiplier = outlier_multiplier
        self.severe_multiplier = severe_multiplier

    def detect(self, engine: BenchmarkEngine, kpi_name: str) -> list[Alert]:
        snapshots = engine.all_snapshots()
        if len(snapshots) < 3:
            # Zu wenig Daten fuer IQR-Statistik
            return []

        q1, median, q3 = engine.quantiles(kpi_name)
        iqr = q3 - q1
        if iqr == 0:
            # Degenerate case: all values identical -> no outliers
            return []

        lower_outlier = q1 - self.outlier_multiplier * iqr
        upper_outlier = q3 + self.outlier_multiplier * iqr
        lower_severe = q1 - self.severe_multiplier * iqr
        upper_severe = q3 + self.severe_multiplier * iqr

        alerts: list[Alert] = []
        for snap in snapshots:
            val = getattr(snap, kpi_name)
            if val < lower_outlier or val > upper_outlier:
                direction = "above" if val > upper_outlier else "below"
                if val < lower_severe or val > upper_severe:
                    sev = "HIGH"
                else:
                    sev = "LOW"
                alerts.append(
                    Alert(
                        tenant_id=snap.tenant_id,
                        kpi_name=kpi_name,
                        value=val,
                        median=median,
                        q1=q1,
                        q3=q3,
                        iqr=iqr,
                        severity=sev,
                        direction=direction,
                    )
                )
        return alerts

    def detect_all(self, engine: BenchmarkEngine) -> dict[str, list[Alert]]:
        """Run detection across adr, occupancy, revpar."""
        return {
            "adr": self.detect(engine, "adr"),
            "occupancy": self.detect(engine, "occupancy"),
            "revpar": self.detect(engine, "revpar"),
        }
