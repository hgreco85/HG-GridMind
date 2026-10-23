# HG GridMind — Autonomous AI Incident Commander

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Tests: 100% Offline](https://img.shields.io/badge/Unit%20Tests-9%2F9%20PASS-brightgreen.svg)]()
[![Generalization Benchmark](https://img.shields.io/badge/Adversarial%20Benchmark-24%2F24%20PASS-success.svg)]()
[![Challenge](https://img.shields.io/badge/Challenge%2002-The%20Agent%20That%20Can%20Explain%20Why-orange.svg)]()
[![Zetaris](https://img.shields.io/badge/Zetaris-Zero--ETL%20Virtual%20SQL-blue.svg)]()
[![Meterless](https://img.shields.io/badge/Meterless-Context%20Engines-purple.svg)]()
[![NVIDIA Nemotron](https://img.shields.io/badge/NVIDIA%20Nemotron-Causal%20Reasoning-green.svg)]()
[![Cursor](https://img.shields.io/badge/Cursor-IDE%20Verified-blue.svg)]()
[![Spend](https://img.shields.io/badge/Spend-$0.00%20USD-success.svg)]()

> **Evidence-linked, auditable operations investigator with active hypothesis falsification, fail-closed human oversight, and zero hallucinated root causes.**  
> Built for the **Open Agent Hackathon 2026** (**Challenge 02: *The Agent That Can Explain Why***).

---

## Live Links for Evaluators & Judges

- **Public Interactive Demo (HTTPS):** [https://hgreco85.github.io/HG-GridMind/](https://hgreco85.github.io/HG-GridMind/)
- **Interactive Pitch Deck (7 Slides):** [https://hgreco85.github.io/HG-GridMind/docs/SLIDES.html](https://hgreco85.github.io/HG-GridMind/docs/SLIDES.html)
- **Official Demo Video (2m 32s · 720p HD):** Embedded directly on the live demo page and located at [`docs/hg_gridmind_demo_video.webm`](docs/hg_gridmind_demo_video.webm).
- **Code Repository:** [https://github.com/hgreco85/HG-GridMind](https://github.com/hgreco85/HG-GridMind)
- **Participant:** **Hernán Francisco Greco** (`@hgreco85`) | Team HG Stack

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
|    - Dynamic physical constraint evaluation across continuous sensor invariants   |
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

### Technical Disclosure & Sponsor Honesty
- **Zetaris:** Implemented as a Virtual Data Fabric Adapter & Lightning SQL dialect engine over in-place silos. Organizer cloud registry remains in `[TBC]`; no remote cloud credentials were provided.
- **Meterless:** Native open-source context protocol implementation in local Python (`H-MEM`, `Markovian`, `World Model`).
- **NVIDIA Nemotron:** Dual-mode causal engine executing physics-grounded threshold rules by default (ensuring $0.00 spend and zero stochasticity), with a live connector ready for OpenAI-compatible / NIM inference.
- **Cursor:** Development environment toolchain (v3.19.7).

---

## 3. Generalization & Adversarial Benchmark (Anti-Overfitting)

To mathematically verify that GridMind is **generalizable and not overfitted** to a single demonstration, the test suite executes **24 evaluations** (4 realistic anchor topologies + 20 continuous parametric variations):

| Scenario | Condition / Variation | Agent Finding | Outcome & Action |
|---|---|---|---|
| **`INC-8812`** | Phase B Unbalance + Loose Lug | **H1 & H2 Refuted · H3 Confirmed** | Transformer healthy; $249,850 USD saved via terminal torque. |
| **`INC-9041`** | High-Energy Arc + Buchholz Trip | **H1 Confirmed (C2H2 = 14.5 ppm)** | Catastrophic internal breakdown; re-energization locked; replacement mandatory. |
| **`INC-7720`** | 3-Phase Balanced Feeder Fault | **H2 Confirmed (1600A balanced)** | Downstream car pole collision; transformer 100% undamaged; feeder section isolated. |
| **`INC-5501`** | Missing DGA Chemistry Data | **Strict Abstention (Zero Hallucination)** | Diagnosis refused due to insufficient sensor proof; manual sampling requested. |
| **`Parametric 1-20`** | Continuous Random Distributions of $I, C_2H_2, \Delta T$ | **100% Physical Rule Match** | Physics-based invariant classification without static string reliance. |

Run the 24-case benchmark with:
```bash
python evaluator.py
```

---

## 4. Instructions for Hackathon Judges

Judges can verify the entire project in less than 60 seconds with zero accounts, zero API keys, and zero spend ($0.00):

### A. Run Unit Test Suite (9 tests in ~0.25s):
```bash
python main.py test
```

### B. Run Generalization & Adversarial Benchmark (24 evaluations):
```bash
python evaluator.py
```

### C. Run CLI Investigation (Tests Fail-Closed & Human Signoff):
```bash
# Test 1: Fail-closed safety (dispatch blocked without human token)
python main.py run

# Test 2: Authorized dispatch with operator sign-off
python main.py run --signoff --operator "Hernán Francisco Greco"
```

### D. Open Public Web Demo (No install required):
Visit **[https://hgreco85.github.io/HG-GridMind/](https://hgreco85.github.io/HG-GridMind/)**.

---

## 5. Scope & Compliance

- **Track:** Challenge 02 — *The Agent That Can Explain Why*.
- **Participant:** Hernán Francisco Greco (`@hgreco85`).
- **Isolation:** Standalone public repository decoupled from internal trading systems.
- **Data Disclosure:** 100% synthetic utility grid incident records (`fixtures/`); no proprietary EDENOR or customer data.
- **Cost Invariant:** $0.00 incremental spend throughout.
- **License:** MIT License. See [LICENSE](LICENSE) for details.
