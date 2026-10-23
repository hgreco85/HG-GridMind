# HG GridMind — Autonomous AI Incident Commander

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Tests: 100% Offline](https://img.shields.io/badge/Tests-7%2F7%20PASS-brightgreen.svg)]()
[![Challenge](https://img.shields.io/badge/Challenge%2002-The%20Agent%20That%20Can%20Explain%20Why-orange.svg)]()
[![Zetaris](https://img.shields.io/badge/Zetaris-Zero--ETL%20Virtual%20SQL-blue.svg)]()
[![Meterless](https://img.shields.io/badge/Meterless-Context%20Engines-purple.svg)]()
[![NVIDIA Nemotron](https://img.shields.io/badge/NVIDIA%20Nemotron-Causal%20Reasoning-green.svg)]()
[![Cursor](https://img.shields.io/badge/Cursor-IDE%20Verified-blue.svg)]()
[![Spend](https://img.shields.io/badge/Spend-$0.00%20USD-success.svg)]()

> **Evidence-linked, auditable operations investigator with active hypothesis falsification, fail-closed human oversight, and zero hallucinated root causes.**  
> Built for the **Open Agent Hackathon 2026** (**Challenge 02: *The Agent That Can Explain Why***).

---

## 1. Problem Statement

In electrical power utilities, mission-critical substations, and energy grids, sudden relay protection trips trigger high-stakes operational confusion. Under pressure, dispatchers and control room operators frequently default to catastrophic failure assumptions—such as concluding that a tripping distribution transformer has suffered destructive internal winding dielectric insulation breakdown.

Such misdiagnoses trigger massive, unnecessary capital expenditures ($250,000+ per unit replacement) and prolonged multi-day blackouts for downstream customers while perfectly healthy equipment is taken out of service.

Conventional LLM chatbots fail catastrophically in this domain: they exhibit confirmation bias, hallucinate non-existent SCADA records, fabricate physical causes, and offer zero verifiable mathematical grounding.

**HG GridMind** introduces an auditable, causal AI Incident Commander that explicitly explains **why** an operational disturbance occurred by combining three pillars:
1. **Zero-ETL Virtual Data Federation (Zetaris):** Queries fragmented, in-place operational data across SCADA telemetry, maintenance oil chromatography (DGA), and work order dispatch databases using a single Lightning SQL abstraction with exact row-level citations (`row_id`).
2. **Causal Reasoning & Active Falsification (Meterless + NVIDIA Nemotron):** Utilizes Meterless local context engines (`H-MEM` for timeline structuring, `Markovian` for operational state transitions, and `World Model` for grid topology assertions) driving NVIDIA Nemotron to formulate rival operational theories and actively falsify rival hypotheses against physical sensor counter-proof.
3. **Fail-Closed Human Approval Gate (HG Operator Core):** Strictly disallows autonomous grid switching or maintenance dispatch without a cryptographically verified operator sign-off token (`HumanApprovalGate`), ensuring safety-critical human oversight.

---

## 2. Architecture & Sponsor Technologies

```
+-----------------------------------------------------------------------------------+
|                            OPERATIONAL SILOS & DATA SOURCES                       |
|   [Tickets DB: Interrupciones]    [Mantenimiento: DGA/IR]    [SCADA: Telemetría]  |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| 1. DATA LAYER (Zetaris Virtual Data Fabric)                                       |
|    - Zero-ETL Lightning SQL queries over distributed silos in place               |
|    - Deterministic schema mapping with exact row-level citations (Row IDs)        |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| 2. CONTEXT LAYER (Meterless Context Protocol)                                     |
|    - H-MEM: Hierarchical chronological event memory                               |
|    - Markovian Engine: State transitions (Normal -> Heating -> Imbalance -> Trip) |
|    - World Model: Network topology constraints & physical laws                    |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| 3. REASONING LAYER (NVIDIA Nemotron Causal Engine)                                |
|    - Generation of 3 competing operational hypotheses (H1, H2, H3)                |
|    - Active falsification: testing initial claims against physical counter-proof  |
|    - Explainability synthesis answering WHY                                       |
+-----------------------------------------------------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| 4. CONTROL LAYER (HG Operator Architecture)                                       |
|    - Deterministic Evidence Validator (zero fabricated citations)                 |
|    - Fail-Closed Human Approval Gate (remediation locked until human signoff)     |
|    - Durable ACK & audit trail logging (HG-GRIDMIND-ACK)                          |
+-----------------------------------------------------------------------------------+
```

- **Zetaris:** Virtual query federation joining customer tickets, chromatographic oil analysis (DGA), thermography logs, and SCADA telemetry in one pass.
- **Meterless:** Local context engines (`H-MEM`, `Markovian`, `World Model`) providing structured physical constraints.
- **NVIDIA Nemotron:** Multi-step causal reasoning engine formulating competing hypotheses and refuting rival theories.
- **Cursor:** Development environment utilizing AI-assisted developer workflows with strict zero-cost discipline.

---

## 3. Case Study: Incident `INC-2026-UTIL-8812`

1. **Initial Symptom:** Tripping of feeder breaker B-12 on distribution transformer TR-404. Initial human suspicion: *Internal dielectric breakdown / oil overheating*.
2. **Federated Evidence Retrieval (Zetaris):**
   - `MAINT-ROW-99182`: DGA test from 2026-10-18 shows normal combustible gas levels (Hydrogen 12 ppm, Acetylene 0.1 ppm). **Falsifies internal electrical arc or thermal degradation.**
   - `MAINT-ROW-99204`: Infrared thermography from 2026-10-19 reports hot spot on low-voltage neutral bushing ($+42^\circ\text{C}$ over ambient) due to a loose terminal connection.
   - `SCADA-ROW-55102`: Telemetry records severe phase unbalance (Phase B: $445.8\text{ A}$ vs Phase A: $210.4\text{ A}$), forcing $268.1\text{ A}$ through the neutral terminal.
3. **Verified Causal Verdict:** The transformer core and windings are physically healthy. The issue is severe neutral terminal overheating caused by Phase B unbalance acting upon a high-resistance loose terminal.
4. **Actionable Remediation:** Rebalance feeder loads to auxiliary bus and schedule a 15-minute de-energization window for terminal torque re-tightening. Equipment replacement is avoided, saving **$249,850 USD**.

---

## 4. Instructions for Hackathon Judges

Judges can verify the entire project in less than 60 seconds with zero accounts, zero API keys, and zero spend ($0.00):

### A. Run Test Suite (7 tests in ~0.07s):
```bash
python main.py test
```

### B. Run CLI Investigation (Tests Fail-Closed & Human Signoff):
```bash
# Test 1: Fail-closed safety (dispatch blocked without human token)
python main.py run

# Test 2: Authorized dispatch with operator sign-off
python main.py run --signoff --operator "Judge Evaluator"
```

### C. Launch Interactive Web Dashboard:
```bash
python main.py web --port 8080
```
Open **[http://localhost:8080](http://localhost:8080)** (or double-click `web/index.html`).

### D. Open Pitch Deck (7 Interactive Slides):
Double-click `docs/SLIDES.html` in any web browser.

---

## 5. Scope & Compliance

- **Track:** Challenge 02 — *The Agent That Can Explain Why*.
- **Isolation:** Standalone public repository decoupled from internal trading systems.
- **Data Disclosure:** 100% synthetic utility grid incident records (`fixtures/`); no proprietary EDENOR or customer data.
- **Cost Invariant:** $0.00 incremental spend throughout.
- **License:** MIT License. See [LICENSE](LICENSE) for details.
