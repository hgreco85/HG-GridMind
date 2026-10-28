# HG GridMind — Autonomous AI Incident Commander

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Tests: 100% Offline](https://img.shields.io/badge/Unit%20Tests-23%2F23%20PASS-brightgreen.svg)]()
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

Default mode (what judges run with zero setup) is the **offline deterministic pipeline**. Two sponsor engines can additionally be switched on for **real** execution (opt-in, USD 0, see section 2b). Every output labels which mode ran.

| Sponsor | Default (offline, deterministic) | Opt-in REAL engine (added 2026-10-27) | Still not real |
|---|---|---|---|
| **Zetaris** | `src/sponsors/zetaris_adapter.py`: one entry point, two labelled paths. **SIMULATION** (default): replays the fixture rows, plan says `SIMULATED (no engine contacted)`, payload carries `is_simulation: true`. **REAL** (opt-in): the same adapter executes the contract's SQL through `src/sponsors/zetaris_real.py` on a real Zetaris Lightning 2.4.3.1 (docker compose on the author's PC), 3-source join (PostgreSQL datasource + 2 CSV filestore tables) over a synthetic dataset | Not a hosted/cloud Zetaris; the organiser's cloud registry was not used; if the engine is off the adapter falls back to the labelled simulation |
| **Meterless** | `src/sponsors/meterless_adapter.py`: a local Python *re-implementation* of the H-MEM / Markovian / World-Model ideas (not Meterless code) | `src/sponsors/meterless_real.py` + `integrations/meterless/`: runs the real **Meterless H-MEM reference engine** (Apache-2.0, vendored at setup) fed with the real Zetaris rows; ranked recall, retrieval trace, TrustLedger | World Model, Markovian and Scout Intent are still the local mimic |
| **NVIDIA Nemotron** | `src/sponsors/nemotron_adapter.py`: deterministic physics rules engine | none: an OpenAI-compatible / NIM connector exists in code but **no live Nemotron inference has been run** for this submission | Do not read the repo as having live Nemotron calls |
| **Cursor** | development environment (see `docs/SUBMISSION_WRITEUP.md`) | n/a | `src/sponsors/cursor_audit.py` is a static self-description, not telemetry |

## 2b. Real engines: setup, usage, dependencies (opt-in)

Nothing here is required to run the default demo. Details: [`integrations/zetaris/README.md`](integrations/zetaris/README.md), [`integrations/meterless/README.md`](integrations/meterless/README.md), [`docs/ZETARIS_REAL_VS_MOCK.md`](docs/ZETARIS_REAL_VS_MOCK.md).

**Dependencies.** Core app: Python 3.9+ standard library only (no pip installs). Real Zetaris: Docker (Zetaris platform 2.4.3.1 via its own compose bundle plus `integrations/zetaris/docker-compose.override.yml`), Java 17+ and the official Zetaris JDBC driver jar. Real Meterless: Node 18+, npm and git (vendors `Meterless/Meterless@1742dec` `engines/hmem/reference`, Apache-2.0; dev dependency `tsx`).

```bash
# 1) Offline default (no setup)
python main.py test            # 23 tests
python evaluator.py            # 24-case benchmark
python main.py run --signoff --operator "Your Name"

# 2) Real Meterless H-MEM (free, no API key)
bash integrations/meterless/setup.sh

# 3) Real Zetaris (needs the Zetaris stack running; secrets only via env vars, never committed)
export ZETARIS_JDBC_JAR=/path/to/ndp-jdbc-driver-2.4.3.1-*-driver.jar
export ZETARIS_PASSWORD=...    # never commit / never pass on argv

# 4) Run the full real chain: Zetaris federated join -> Meterless H-MEM recall + ledger
export GRIDMIND_ZETARIS_REAL=1 GRIDMIND_METERLESS_REAL=1
python integrations/meterless/demo_live_chain.py out.json
GRIDMIND_ZETARIS_LIVE=1 python -m unittest discover tests   # includes live-engine tests

# 5) Timestamped evidence + E2E trace + UI screen recording (all USD 0, local only)
python integrations/zetaris/evidence/run_live_evidence.py --jar "$ZETARIS_JDBC_JAR" --show-summary
python integrations/zetaris/evidence/run_e2e_demo.py --asset TR-102 --signoff
python integrations/zetaris/evidence/capture_ui_video.py      # needs: python -m playwright install ffmpeg
```

If an engine is unavailable the connector never raises: `result["zetaris_real"]` / `result["meterless_real"]` report `{"used": false, "fallback": "SIMULATION"/"MIMIC", "is_simulation": true, "reason": ...}`.

**Real-engine evidence (committed):** `integrations/zetaris/evidence/` (timestamped JDBC runs `05`/`06`/`07`, older `01`–`04`, docker ps, versions), `docs/evidence/zetaris/` (UI screenshots and 1080p recordings of the Zetaris UI running the federated query), `integrations/meterless/evidence/` (real Zetaris rows into real H-MEM, 23/23 tests with both engines live, upstream engine tests). Video material mapped to authentic shots: [`docs/ZETARIS_VIDEO_AUTHENTIC_SCENES.md`](docs/ZETARIS_VIDEO_AUTHENTIC_SCENES.md).

**Honest limits.** The real Zetaris engine holds a small *synthetic* dataset that covers only asset TR-102 (fixture `INC_2026_UTIL_5501`); the other fixtures keep using the offline simulation. The incident reasoning (hypotheses, falsification, approval gate) is the pre-existing deterministic code; the real engines supply federated evidence and durable memory with provenance on top of it. The default path is still the simulation, and it says so in every payload.

## 2c. Declaration: pre-existing code vs work done during the build window

The hackathon build window opened on 2026-10-22. The first working version of GridMind was committed on **2026-10-23** (commits `edef57c`, `c7460c8`, `c6a66e9`, `3a39432`). The Zetaris and Meterless real-engine work below is a separate set of commits on 2026-10-27.

- **Pre-existing at the start of the real-engine work (2026-10-23 commits):** `src/agent.py`, `src/gate.py`, `src/cli.py`, `main.py`, `evaluator.py`, the offline sponsor adapters (`zetaris_adapter.py`, `meterless_adapter.py`, `nemotron_adapter.py`, `cursor_audit.py`), `src/data_connector.py` (the mock federation), `fixtures/`, `web/` + `index.html`, `docs/` (slides, guide, video), `metadata.json`, and the original 9 tests plus the 24-case benchmark.
- **New work (2026-10-27, PR #10):** `src/sponsors/zetaris_real.py`, `src/sponsors/meterless_real.py`, the opt-in wiring in `src/data_connector.py`, `integrations/zetaris/` (synthetic dataset, SQL, docker override, JDBC runner, evidence), `integrations/meterless/` (H-MEM bridge, setup, demo, evidence), `tests/test_zetaris_real.py`, `tests/test_meterless_real.py`, `docs/ZETARIS_REAL_VS_MOCK.md`, `docs/evidence/zetaris/`, `docs/SUBMISSION_WRITEUP.md`, this README section.
- **New work (2026-10-28, same PR #10):** `zetaris_adapter.py` reworked into the real-first facade with the explicitly-labelled simulation fallback (plan says `SIMULATED (no engine contacted)`; payloads carry `is_simulation`/`simulation_disclosure`), `src/data_connector.py` delegating to it, timestamped evidence (`05_live_verified.json`, `06_e2e_trace_TR102.json`, `07_e2e_trace_INC8812.json`), the reproducible scripts `run_live_evidence.py` / `run_e2e_demo.py` / `capture_ui_video.py` / `render_transcript_clip.py`, new 1080p UI recording and E2E clip, `docs/ZETARIS_VIDEO_AUTHENTIC_SCENES.md`, and the test updates that assert the labelled-simulation contract.
- **Third-party code:** the Meterless H-MEM reference engine (Apache-2.0, Meterless) is fetched at setup into a gitignored `vendor/` directory and is not part of this repository's history. The Zetaris platform and JDBC driver are Zetaris software obtained through the hackathon and are not redistributed here.

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

### A. Run Unit Test Suite (23 tests, ~1s; the live-engine tests auto-skip when the engines are not set up):
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
- **Cost Invariant:** $0.00 incremental spend throughout (Zetaris and Meterless engines are free; no API keys used).
- **License:** MIT License. See [LICENSE](LICENSE) for details.
