# Instructions for Hackathon Judges — HG GridMind

Welcome to the evaluation harness for **HG GridMind** (Open Agent Hackathon 2026, **Challenge 02: The Agent That Can Explain Why**).

The project is designed to be **100% reproducible offline with zero setup friction, zero paid APIs, zero external secrets, and zero credit card requirements ($0.00 USD spend)**.

---

## 1. Quick Verification (30 Seconds)

Clone the repository and run the test suite using standard Python (3.10+):

```bash
git clone https://github.com/hgreco85/HG-GridMind.git
cd HG-GridMind
python main.py test
```

Expected Output:
```text
test_causal_investigation_and_evidence_citations ... ok
test_cursor_environment_audit ... ok
test_human_approval_gate_fail_closed_without_token ... ok
test_human_approval_gate_passes_with_authenticated_token ... ok
test_meterless_context_engines ... ok
test_nemotron_causal_reasoner_falsification ... ok
test_zetaris_virtual_data_fabric_query_plan ... ok

----------------------------------------------------------------------
Ran 7 tests in 0.070s
OK
```

---

## 2. Interactive CLI Investigation Demo

Execute the end-to-end causal reasoning pipeline directly in your terminal:

### A. Fail-Closed Test (Attempt dispatch without human sign-off):
```bash
python main.py run
```
You will observe:
1. Zetaris queries SCADA, DGA, and tickets in-place without data movement.
2. Nemotron formulates 3 rival hypotheses and actively falsifies H1 and H2 using physical citations (`MAINT-ROW-99182` and `SCADA-ROW-55102`).
3. Causal verdict refutes the $250,000 transformer replacement order.
4. Autonomous physical dispatch is **BLOCKED** by the `HumanApprovalGate` (Fail-closed invariant).

### B. Authorized Dispatch with Human Sign-off:
```bash
python main.py run --signoff --operator "Judge Evaluator"
```
You will observe:
1. Human sign-off token `HUMAN-SIGNOFF-<HASH>` issued.
2. Corrective switching order authorized and dispatched.
3. Cryptographic audit trail generated (`HG-GRIDMIND-ACK-<HASH>`).

---

## 3. Interactive Web Dashboard

Launch the local web dashboard:
```bash
python main.py web --port 8080
```
Open **[http://localhost:8080](http://localhost:8080)** in your browser (or simply double-click `web/index.html` directly).

Features available to judges:
- **Case Switcher:** Toggle between the primary incident (`INC-2026-UTIL-8812`) and adversarial stress tests (missing sensor data triggers strict abstention instead of hallucination).
- **Zetaris Federated Tables:** Inspect live row-level citations for SCADA telemetry and DGA oil tests.
- **Rival Hypothesis Falsification Panel:** Real-time visual comparison of H1 (internal fault), H2 (short circuit), and H3 (loose neutral connection under Phase B unbalance).
- **Human Approval Gate Simulator:** Test both the fail-closed rejection and the operator authorization flow.

---

## 4. Sponsor Technologies Audit

| Sponsor | Integration Mechanism | Verification Method |
|---|---|---|
| **Zetaris** | Virtual SQL Federation joining 3 silos Zero-ETL | `src/sponsors/zetaris_adapter.py` & `test_zetaris_virtual_data_fabric_query_plan` |
| **Meterless** | H-MEM chronological memory & Markovian state transitions | `src/sponsors/meterless_adapter.py` & `test_meterless_context_engines` |
| **NVIDIA Nemotron** | Causal hypothesis generation & active falsification | `src/sponsors/nemotron_adapter.py` & `test_nemotron_causal_reasoner_falsification` |
| **Cursor** | AI-assisted development environment | `src/sponsors/cursor_audit.py` & `test_cursor_environment_audit` |

Zero incremental cost ($0.00 USD) guaranteed throughout development and evaluation.
