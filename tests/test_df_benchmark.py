"""Tests fuer df-hotel-benchmark-tracker [CRUX-MK]."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.adapter_orchestrator import run_once
from src.alert_engine import Alert, IQROutlierDetector
from src.audit_logger import AuditLogger
from src.benchmark_engine import (
    BenchmarkEngine,
    HotelKPI,
    is_real_mode_enabled,
    load_mock_kpis,
)


def test_hotel_kpi_revpar_computation() -> None:
    kpi = HotelKPI(tenant_id="t", name="T", region="DE", adr=200.0, occupancy=0.8)
    assert kpi.revpar == 160.0


def test_engine_rejects_invalid_occupancy() -> None:
    eng = BenchmarkEngine()
    with pytest.raises(ValueError):
        eng.add_snapshot(HotelKPI(tenant_id="x", name="X", region="DE", adr=100, occupancy=1.5))
    with pytest.raises(ValueError):
        eng.add_snapshot(HotelKPI(tenant_id="y", name="Y", region="DE", adr=100, occupancy=-0.1))


def test_engine_rejects_negative_adr() -> None:
    eng = BenchmarkEngine()
    with pytest.raises(ValueError):
        eng.add_snapshot(HotelKPI(tenant_id="x", name="X", region="DE", adr=-1, occupancy=0.5))


def test_engine_median_and_quantiles() -> None:
    eng = BenchmarkEngine()
    for i, v in enumerate([100, 150, 200, 250, 300]):
        eng.add_snapshot(HotelKPI(tenant_id=f"t{i}", name=f"T{i}", region="DE", adr=v, occupancy=0.8))
    assert eng.median("adr") == 200.0
    q1, med, q3 = eng.quantiles("adr")
    assert q1 == 150.0
    assert med == 200.0
    assert q3 == 250.0


def test_engine_values_for_kpi_validation() -> None:
    eng = BenchmarkEngine()
    eng.add_snapshot(HotelKPI(tenant_id="x", name="X", region="DE", adr=100, occupancy=0.5))
    with pytest.raises(ValueError):
        eng.values_for("unknown_kpi")


def test_iqr_detector_validates_multipliers() -> None:
    with pytest.raises(ValueError):
        IQROutlierDetector(outlier_multiplier=0)
    with pytest.raises(ValueError):
        IQROutlierDetector(outlier_multiplier=1.5, severe_multiplier=1.0)


def test_iqr_detector_returns_empty_for_too_few_samples() -> None:
    eng = BenchmarkEngine()
    eng.add_snapshot(HotelKPI(tenant_id="x", name="X", region="DE", adr=100, occupancy=0.5))
    detector = IQROutlierDetector()
    alerts = detector.detect(eng, "adr")
    assert alerts == []


def test_iqr_detector_no_alerts_when_uniform() -> None:
    eng = BenchmarkEngine()
    # All same -> IQR=0 -> no outliers
    for i in range(5):
        eng.add_snapshot(HotelKPI(tenant_id=f"t{i}", name=f"T{i}", region="DE", adr=150, occupancy=0.7))
    detector = IQROutlierDetector()
    alerts = detector.detect(eng, "adr")
    assert alerts == []


def test_iqr_detector_flags_outlier_high() -> None:
    eng = BenchmarkEngine()
    for i, v in enumerate([140, 145, 150, 155, 160, 1000]):
        eng.add_snapshot(HotelKPI(tenant_id=f"t{i}", name=f"T{i}", region="DE", adr=v, occupancy=0.7))
    detector = IQROutlierDetector()
    alerts = detector.detect(eng, "adr")
    flagged = {a.tenant_id for a in alerts}
    assert "t5" in flagged
    high = [a for a in alerts if a.tenant_id == "t5"][0]
    assert high.direction == "above"
    assert high.severity == "HIGH"


def test_iqr_detector_flags_outlier_low() -> None:
    eng = BenchmarkEngine()
    for i, v in enumerate([200, 210, 220, 230, 240, 5]):
        eng.add_snapshot(HotelKPI(tenant_id=f"t{i}", name=f"T{i}", region="DE", adr=v, occupancy=0.7))
    detector = IQROutlierDetector()
    alerts = detector.detect(eng, "adr")
    flagged = [a for a in alerts if a.tenant_id == "t5"]
    assert len(flagged) == 1
    assert flagged[0].direction == "below"


def test_iqr_detector_detect_all_keys() -> None:
    eng = BenchmarkEngine()
    for kpi in load_mock_kpis():
        eng.add_snapshot(kpi)
    detector = IQROutlierDetector()
    result = detector.detect_all(eng)
    assert set(result.keys()) == {"adr", "occupancy", "revpar"}


def test_audit_logger_chain_intact(tmp_path: Path) -> None:
    audit = AuditLogger(tmp_path / "audit.jsonl")
    audit.log({"event": "a"})
    audit.log({"event": "b"})
    assert audit.verify_chain() is True


def test_audit_logger_detects_tampering(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    audit = AuditLogger(path)
    audit.log({"event": "a"})
    audit.log({"event": "b"})
    lines = path.read_text().splitlines()
    rec = json.loads(lines[0])
    rec["event"] = "tampered"
    lines[0] = json.dumps(rec)
    path.write_text("\n".join(lines) + "\n")
    audit2 = AuditLogger(path)
    assert audit2.verify_chain() is False


def test_real_mode_default_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DF_BENCHMARK_REAL_PMS_ENABLED", raising=False)
    assert is_real_mode_enabled() is False
    monkeypatch.setenv("DF_BENCHMARK_REAL_PMS_ENABLED", "true")
    assert is_real_mode_enabled() is True


def test_run_once_smoke(tmp_path: Path) -> None:
    result = run_once(tmp_path / "audit.jsonl")
    assert result["hotels_tracked"] == 5
    assert result["chain_intact"] is True
    # mock-5 ist ein klarer ADR-Outlier (410 vs Median ~189)
    adr_alerts = result["alerts_by_kpi"]["adr"]
    flagged = {a.tenant_id for a in adr_alerts}
    assert "mock-5" in flagged


def test_run_once_alerts_well_formed(tmp_path: Path) -> None:
    result = run_once(tmp_path / "audit.jsonl")
    for kpi_name, alerts in result["alerts_by_kpi"].items():
        for a in alerts:
            assert isinstance(a, Alert)
            assert a.kpi_name == kpi_name
            assert a.severity in {"LOW", "HIGH"}
            assert a.direction in {"above", "below"}
