# df-hotel-benchmark-tracker — Output [CRUX-MK]
*Autonom aktiviert 2026-06-05T14:13:21.909934+00:00 | ollama-local/qwen2.5:14b-instruct*

# Dark-Factory Dokumentation: df-hotel-benchmark-tracker

## Zweck und Architektur

Die Dark-Factory `df-hotel-benchmark-tracker` ist eine Sandbox-Umgebung, di
die das Tracking von KPIs (Key Performance Indicators) für verschiedene Hot
Hotels durchführt. Der Fokus liegt auf dem RevPAR (Revenue per Available Ro
Room), der Occupancy Rate sowie dem ADR (Average Daily Rate). Die Factory i
identifiziert statistische Ausreißer in diesen Metriken unter Verwendung de
der 1,5x IQR-Rule und generiert entsprechende Warnungen bei auffälligen Abw
Abweichungen im Vergleich zu einer Peer-Gruppe.

### Architektur

Die Factory besteht aus den folgenden Hauptkomponenten:

- **benchmark_engine.py:** Enthält die Mock-Daten für die KPIs RevPAR, Occu
Occupancy und ADR.
- **alert_engine.py:** Implementiert die Ausreißererkennung basierend auf d
der 1,5x IQR-Rule.
- **adapter_orchestrator.py:** Entry Point des LaunchAgents, steuert den Wo
Workflow.
- **audit_logger.py:** Nimmt HMAC-SHA256 JSONL-Auditsprotokolle für eine ve
verbesserte Sicherheit und Überwachung vor.

## KPIs

Die Factory verwendet die folgenden KPIs zur Auswertung:

1. **RevPAR (Revenue per Available Room):** Berechnet durch Multiplikation 
von ADR und Occupancy Rate.
2. **Occupancy:** Gibt an, wie viele Zimmer pro Hotel belegt sind im Verhäl
Verhältnis zu den verfügbaren Räumen.
3. **ADR (Average Daily Rate):** Durchschnittlicher Ertrag pro belegtem Zim
Zimmer.

## Ausreißererkennung

Die Factory identifiziert Ausreißer für jede KPI über alle Hotels mit Hilfe
Hilfe der 1,5x IQR-Rule:

- Berechnet das erste Quartil (Q1) und dritten Quartil (Q3).
- Bestimmt den Interquartilsabstand (IQR = Q3 - Q1).
- Eine Metrik wird als Ausreißer identifiziert, wenn sie kleiner als `Q1 - 
1.5*IQR` oder größer als `Q3 + 1.5*IQR` ist.
- Die Severity-Level der Warnungen wird auf "HIGH" gesetzt, falls die Diffe
Differenz zwischen dem Wert und dem Median größer als `3*IQR` ist.

## Einrichtung und Ausführung

Die Factory kann ohne echte Service-Aufrufe im Sandbox-Modus ausgeführt wer
werden. Sie erzeugt Mock-Daten für KPIs und führt eine vollständige Überwac
Überwachung durch, die ohne direkten Zugriff auf Live-PMS-Daten (Property M
Management System) auskommt.

### Befehle zum Starten und Testen

- **Starten:**
  ```bash
  python3 -m src.adapter_orchestrator
  ```
  
- **Tests durchführen:**
  ```bash
  python3 -m pytest tests/ -q
  ```

Diese Dark-Factory folgt streng den CRUX-MK-Standards und erfüllt die Krite
Kriterien K11-K16 vollständig sowie LC1-LC5 für lose Kopplung.