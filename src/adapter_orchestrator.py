"""Adapter-Orchestrator: LaunchAgent Entry-Point [CRUX-MK]."""

from __future__ import annotations

import sys
import time
from dataclasses import asdict
from pathlib import Path

from .alert_engine import IQROutlierDetector
from .audit_logger import AuditLogger
from .benchmark_engine import BenchmarkEngine, is_real_mode_enabled, load_mock_kpis


def run_once(audit_path: Path) -> dict:
    """LaunchAgent Entry-Point: load KPIs, detect outliers, log alerts."""
    audit = AuditLogger(audit_path)
    audit.log({"event": "run_start", "real_mode_enabled": is_real_mode_enabled()})

    engine = BenchmarkEngine()
    for kpi in load_mock_kpis():
        engine.add_snapshot(kpi)

    detector = IQROutlierDetector(outlier_multiplier=1.5, severe_multiplier=3.0)
    alerts_by_kpi = detector.detect_all(engine)

    summary = {
        kpi_name: [asdict(a) for a in alerts] for kpi_name, alerts in alerts_by_kpi.items()
    }
    alert_count = sum(len(v) for v in alerts_by_kpi.values())

    audit.log({
        "event": "run_complete",
        "hotels_tracked": len(engine.all_snapshots()),
        "alerts": summary,
        "alert_count": alert_count,
        "source": "mock",
        "checked_at": int(time.time()),
    })

    return {
        "hotels_tracked": len(engine.all_snapshots()),
        "alerts_by_kpi": alerts_by_kpi,
        "alert_count": alert_count,
        "chain_intact": audit.verify_chain(),
    }


def main() -> int:
    """CLI entry-point."""
    audit_path = Path.home() / ".df-hotel-benchmark-tracker" / "audit.jsonl"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    result = run_once(audit_path)
    success = result["hotels_tracked"] > 0 and result["chain_intact"]
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
