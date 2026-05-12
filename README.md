# df-hotel-benchmark-tracker [CRUX-MK]

**Welle:** 47 (W45-B-RETRY)
**Type:** foundation-df
**Sandbox-Default:** ja (Mock-KPI-Daten, kein Real-Service-Call)

## Zweck

Cross-Hotel-KPI-Benchmark-Tracking: RevPAR + Occupancy + ADR pro Hotel.
Outlier-Detection mit 1.5x-IQR-Rule. Generiert Alert-Events bei statistisch
auffaelligen Abweichungen vs Peer-Group.

## Architektur

```
src/
  benchmark_engine.py      # KPI: RevPAR + Occupancy + ADR Mock-Daten
  alert_engine.py          # Outlier-Detection mit 1.5x-IQR-Rule
  adapter_orchestrator.py  # LaunchAgent Entry-Point main()
  audit_logger.py          # HMAC-SHA256 JSONL audit
```

## KPIs

- **RevPAR** = Revenue per Available Room = ADR * Occupancy
- **Occupancy** = belegte / verfuegbare Zimmer
- **ADR** = Average Daily Rate = Revenue / belegte Zimmer

## Outlier-Detection (1.5x IQR-Rule)

Pro KPI ueber alle Hotels:
- Q1 = 25%-Quantil, Q3 = 75%-Quantil, IQR = Q3 - Q1
- Outlier: x < Q1 - 1.5*IQR  ODER  x > Q3 + 1.5*IQR
- Alert-Severity: HIGH wenn |x - median| > 3*IQR

## CRUX-Konformitaet

- **K11-K16:** vollstaendig
- **LC1-LC5:** Lose-Coupling
- **K0_touch:** false (Sandbox-Mock, kein Live-PMS-Read)

## Run

```bash
python3 -m src.adapter_orchestrator
```

## Tests

```bash
python3 -m pytest tests/ -q
```

[CRUX-MK]
