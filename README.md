# HG GridMind — Autonomous AI Incident Commander

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Tests: 100% Offline](https://img.shields.io/badge/Tests-9%2F9%20PASS-brightgreen.svg)]()
[![Benchmark](https://img.shields.io/badge/Adversarial%20Benchmark-4%2F4%20PASS-success.svg)]()
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
|    - Dynamic physical constraint evaluation across sensor invariants              |
|    - Active falsification: refuting rival hypotheses against sensor ground truth  |
|    - Explainability synthesis answering WHY with verified row citations          |
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

## 3. Generalization & Adversarial Evaluation

To prove that GridMind is **generalizable and not overfitted** to a single case, the suite includes an adversarial benchmark evaluating 4 distinct operational scenarios:

| Incident ID | Topology / Condition | Agent Finding | Outcome & Action |
|---|---|---|---|
| **`INC-8812`** | Asymmetrical Load + Loose Lug | **H1 & H2 Refuted · H3 Confirmed** | Transformer healthy; $249,850 USD saved via terminal torque. |
| **`INC-9041`** | High-Energy Arc + Buchholz Trip | **H1 Confirmed (C2H2 = 14.5 ppm)** | Catastrophic internal breakdown; re-energization locked; replacement mandatory. |
| **`INC-7720`** | 3-Phase Balanced Feeder Fault | **H2 Confirmed (1600A balanced)** | Downstream car pole collision; transformer 100% undamaged; feeder section isolated. |
| **`INC-5501`** | Missing DGA Chemistry Data | **Strict Abstention (Zero Hallucination)** | Diagnosis refused due to insufficient sensor proof; manual sampling requested. |

Run the benchmark with:
```bash
python evaluator.py
```

---

## 4. Instructions for Hackathon Judges

Judges can verify the entire project in less than 60 seconds with zero accounts, zero API keys, and zero spend ($0.00):

### A. Run Test Suite (9 tests in ~0.17s):
```bash
python main.py test
```

### B. Run Adversarial Generalization Benchmark (4 topologies):
```bash
python evaluator.py
```

### C. Run CLI Investigation (Tests Fail-Closed & Human Signoff):
```bash
# Test 1: Fail-closed safety (dispatch blocked without human token)
python main.py run

# Test 2: Authorized dispatch with operator sign-off
python main.py run --signoff --operator "Judge Evaluator"
```

### D. Launch Interactive Web Dashboard:
```bash
python main.py web --port 8080
```
Open **[http://localhost:8080](http://localhost:8080)** (or double-click `web/index.html`).

### E. Open Pitch Deck (7 Interactive Slides):
Double-click `docs/SLIDES.html` in any web browser.

---

## 5. Scope & Compliance

- **Track:** Challenge 02 — *The Agent That Can Explain Why*.
- **Isolation:** Standalone public repository decoupled from internal trading systems.
- **Data Disclosure:** 100% synthetic utility grid incident records (`fixtures/`); no proprietary EDENOR or customer data.
- **Cost Invariant:** $0.00 incremental spend throughout.
- **License:** MIT License. See [LICENSE](LICENSE) for details.
