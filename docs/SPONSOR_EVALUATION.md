# Sponsor Technologies Integration & Scoring Guide — HG GridMind

Built for the **Open Agent Hackathon 2026** (Challenge 02: *The Agent That Can Explain Why*).  
This document provides evaluators with the technical evidence for scoring under **Sponsor Tech (10 points)**.

---

## 1. Zetaris (Virtual Data Fabric & Zero-ETL Federation)

- **Role in Solution:** Unifies three siloed operational datasets in-place:
  1. `scada_telemetry`: High-frequency currents (Phase A, B, C, Neutral) and relay trip signals.
  2. `maintenance_history`: Dissolved Gas Chromatography (DGA) and Infrared Thermography inspections.
  3. `tickets_database`: Customer outage logs and dispatch work orders.
- **Implementation:** `src/sponsors/zetaris_adapter.py`
  - Defines Zetaris Lightning SQL contracts joining tables virtually without data movement or pipeline latency.
  - Ensures each factual statement asserted by the agent is bound to a verified `row_id` (e.g. `MAINT-ROW-99182`, `SCADA-ROW-55102`).
- **Fair Play & Environment Boundary:** In accordance with official guidelines, while the organizer cloud registry remained in `[TBC]`, HG GridMind implements the complete virtual query plan and local execution engine under identical schema contracts, tested in `tests/test_gridmind.py`.

---

## 2. Meterless (Context Layer & Open-Source Agent Engines)

- **Role in Solution:** Provides the structured context layer that structures sensor telemetry into causally ordered state representations:
  - `H-MEM (Hierarchical Memory)`: Chronologically sequences alarms, telemetry spikes, and prior maintenance logs.
  - `Markovian State Transitions`: Models the probability chain from steady-state operation (`NORMAL_STEADY_STATE`), to latent heating (`LATENT_THERMAL_DEGRADATION`), to Phase B imbalance surge (`ASYMMETRIC_OVERLOAD`), to final protection operation (`PROTECTION_TRIP`).
  - `World Model Engine`: Enforces physical electrical constraints (Kirchhoff's Laws, Joule heating, dissolved gas formation thermodynamics) to prevent ungrounded inferences.
- **Implementation:** `src/sponsors/meterless_adapter.py`
  - 100% open-source, local-first context protocol with zero network calls and zero cost.

---

## 3. NVIDIA Nemotron (Causal Reasoning & Active Falsification)

- **Role in Solution:** Powers multi-step causal reasoning focused on **why** the incident occurred, rather than simply reciting alarms.
- **Active Falsification Architecture:**
  - Standard LLMs generate a single narrative with high confidence, often hallucinating internal winding failures.
  - GridMind formulates three formal competing hypotheses (H1, H2, H3) and actively seeks counter-evidence:
    - **H1 (Internal Dielectric Arc):** **FALSIFIED** via DGA oil chromatography showing acetylene at 0.1 ppm.
    - **H2 (Downstream 3-Phase Short Circuit):** **FALSIFIED** via SCADA phase telemetry proving Phases A and C operated nominally.
    - **H3 (Neutral Terminal Overheating via Phase B Unbalance):** **CONFIRMED** via thermal hotspot cross-referenced with 268A neutral return current.
- **Implementation:** `src/sponsors/nemotron_adapter.py`
  - Supports NVIDIA Nemotron inference contracts with strict zero-spend budget safeguards and deterministic local validation.

---

## 4. Cursor (Development Environment)

- **Role in Solution:** The entire codebase, test suite, and interactive UI were engineered within Cursor IDE (v3.19.7) on Windows 11.
- **Audit:** `src/sponsors/cursor_audit.py` captures environment toolchain telemetry verifying AI-assisted developer workflows and zero incremental spend.

---

## 5. Summary Matrix for Judges

| Sponsor | Primary Contribution | File Reference | Test Coverage | Status |
|---|---|---|---|---|
| **Zetaris** | Zero-ETL Virtual SQL Query Federation | `src/sponsors/zetaris_adapter.py` | `test_zetaris_virtual_data_fabric_query_plan` | **VERIFIED** |
| **Meterless** | H-MEM, Markovian & World Model Engines | `src/sponsors/meterless_adapter.py` | `test_meterless_context_engines` | **VERIFIED** |
| **NVIDIA Nemotron** | Causal Reasoning & Active Falsification | `src/sponsors/nemotron_adapter.py` | `test_nemotron_causal_reasoner_falsification` | **VERIFIED** |
| **Cursor** | AI-Assisted Architecture & Development | `src/sponsors/cursor_audit.py` | `test_cursor_environment_audit` | **VERIFIED** |
