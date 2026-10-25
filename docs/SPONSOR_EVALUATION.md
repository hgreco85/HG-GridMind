# Sponsor Technologies Integration & Critical Audit — HG GridMind

Built for the **Open Agent Hackathon 2026** (Challenge 02: *The Agent That Can Explain Why*).  
This document provides hackathon judges with a rigorous, honest, and verifiable evaluation of all sponsor technologies under the **Sponsor Tech (10 points)** rubric.

---

## 1. Technical Boundary & Operational Honesty Statement

To adhere to the hackathon's strictest factual standards and prevent misleading claims:
- **No Simulated Claims:** We explicitly disclose which components are live connections vs. local contracts and virtual harnesses.
- **Evidence intent, not a zero-hallucination guarantee:** Local code and tests aim to link factual claims to source row IDs; adversarial and integration validation remain necessary.
- **Zero Cost Invariant ($0.00 USD):** No paid cloud APIs, unauthorized subscriptions, or billable tokens were used.

---

## 2. Zetaris (Virtual Data Fabric & Zero-ETL Federation)

- **Official Hackathon Status:** The official organizer setup document (`Zetaris: Sponsor Overview`) maintained:  
  `[TBC: instance access and the Zetaris documentation will be added to this folder before the build window opens on 22 October.]`  
  No cloud instance credentials or Azure registry secrets were distributed by organizers.
- **HG GridMind Implementation (`src/sponsors/zetaris_adapter.py`):**
  - **Type:** Virtual Data Fabric Contract & Local Lightning SQL Federation Engine.
  - **Functionality:** Executes synthetic-source SQL joins using an in-memory SQLite backend; the SQL contract is Zetaris-inspired but has not been verified against a genuine Zetaris engine or dialect.
  - **Row-Level Citations:** Validates that every factual statement matches an immutable row ID (e.g. `MAINT-ROW-99182`, `SCADA-ROW-55102`, `TICKET-ROW-33019`).
- **Verification boundary:** Local SQL prototype only. A true Zetaris connection, authentication, dialect compatibility and cloud query result are **NOT VERIFIED / BLOCKED**. A URL string does not prove connectivity.

---

## 3. Meterless (Local-First Context Layer & Open-Source Agent Engines)

- **Official Hackathon Status:** Meterless is open-source (`github.com/Meterless/Meterless`). Fully available from day 1.
- **HG GridMind Implementation (`src/sponsors/meterless_adapter.py`):**
  - **Type:** Local Python context engine plus (on the unmerged audit branch) a TypeScript bridge to vendored Meterless reference source. Reference-engine invocation must be distinguished from independently grounded causal conclusions.
  - **Engines Utilized:**
    1. **H-MEM (Hierarchical Memory):** Chronologically orders distributed operational events, establishing causal timelines.
    2. **Markovian State Engine:** Models probability transitions across operational states (Normal -> Thermal Degradation -> Asymmetric Surge -> Protection Trip).
    3. **World Model Engine:** Enforces physical power grid invariants (Kirchhoff's Current Law, Joule heating, and dissolved gas threshold physics).
- **Verification boundary:** The bridge invokes H-MEM, World Model and Markovian reference code, but the Markovian generator currently emits prewritten, incident-independent conclusions. Runtime conformance/E2E checks require captured exit codes and must not count skipped tests as PASS.

---

## 4. NVIDIA Nemotron (Causal Reasoning & Active Falsification)

- **Official Hackathon Status:** Recommended for complex multi-step reasoning.
- **HG GridMind Implementation (`src/sponsors/nemotron_adapter.py`):**
  - **Type:** Hybrid Architecture with Dual-Mode Capability:
    - **Mode 1: Deterministic Physical Causal Engine (Default):** Evaluates physical sensor invariants, generates 3 formal rival hypotheses, and actively refutes incorrect hypotheses using physical evidence (DGA chemistry, current symmetry, thermal delta). Runs 100% offline, deterministic, in under 1 millisecond.
    - **Mode 2: Live LLM Inference Connector:** Compatible with local Ollama (`qwen3.5:4b` / `nemotron` weights) and NVIDIA NIM API endpoints when explicitly enabled.
  - **Factual Integrity Note:** We explicitly disclose that the default offline evaluation runs the deterministic physical rules engine to guarantee instant offline verification ($0.00 USD) without model stochasticity.
- **Verification boundary:** Deterministic causal rules are implemented; genuine live NVIDIA Nemotron inference has **NOT** been verified in this audit.

---

## 5. Cursor (Development Environment)

- **Official Hackathon Status:** Organizer access document remained in `[TBC]`.
- **HG GridMind Implementation (`src/sponsors/cursor_audit.py`):**
  - **Type:** Local Development Toolchain (Cursor IDE v3.19.7 on Windows 11).
  - **Audit:** Automated environment auditor verifies toolchain, inline AI-assisted architecture refactoring, and fail-closed safety authoring.
- **Verification boundary:** Development-workflow attribution and Cursor version must be supported by independent host or build records; a metadata object or Python test alone does not verify IDE use.

---

## 6. Summary Evaluation Matrix for Judges

| Sponsor | Mechanism | Type | Verification Command | Status |
|---|---|---|---|---|
| **Zetaris** | Local SQLite SQL over synthetic data | Local prototype, not official Zetaris | Inspect adapter + run separate authenticated gateway probe if authorized | **CLOUD BLOCKED / NOT VERIFIED** |
| **Meterless** | Vendored H-MEM / World Model / Markovian TS bridge plus Python adapter | Reference engine bridge, scripted reasoning generator | Run official conformance + disconnected-bridge E2E without skips; capture logs | **CODE PRESENT / E2E NOT REVERIFIED HERE** |
| **NVIDIA Nemotron** | Offline rules by default | Deterministic fallback, not model inference | Run rules benchmark; separately prove authorized live inference | **LIVE INFERENCE NOT VERIFIED** |
| **Cursor** | Development environment metadata | Toolchain attestation pending | Collect genuine host/version and provenance log | **NOT INDEPENDENTLY VERIFIED** |
