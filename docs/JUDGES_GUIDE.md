# Instructions for Hackathon Judges — HG GridMind

Welcome to the evaluation harness for **HG GridMind** (Open Agent Hackathon 2026, **Challenge 02: The Agent That Can Explain Why**).

The project is designed to be **100% reproducible offline with zero setup friction, zero paid APIs, zero external secrets, and zero credit card requirements ($0.00 USD spend)**.

---

## 1. Quick Verification (30 Seconds)

Clone the repository and run the unit test suite using standard Python (3.10+):

```bash
git clone https://github.com/hgreco85/HG-GridMind.git
cd HG-GridMind
python main.py test
```

Expected Output:
```text
Ran 9 tests in 0.175s
OK
```

---

## 2. Multi-Scenario Adversarial Benchmark (Generalization Check)

To verify that the agent is **not overfitted** to a single demonstration incident, run the comprehensive 4-scenario evaluator:

```bash
python evaluator.py
```

Evaluates 4 distinct operational topologies:
1. **INC-8812 (Asymmetrical Overload):** Falsifies internal arc, confirms neutral lug overheating, and saves $249,850 USD.
2. **INC-9041 (Catastrophic Arc):** Identifies true internal destructive arc (Acetylene 14.5 ppm + Buchholz), locks re-energization, and mandates immediate replacement.
3. **INC-7720 (Downstream Line Fault):** Identifies 3-phase line contact from vehicle collision; keeps transformer in service.
4. **INC-5501 (Missing Data / Adversarial):** Strictly **abstains** from diagnosing due to missing chemical telemetry, preventing hallucinations.

Expected Output:
```text
BENCHMARK RESULT: 4/4 SCENARIOS PASSED (100% SUCCESS)
Zero overfitting verified.
```

---

## 3. Interactive CLI Investigation Demo

Execute the end-to-end causal reasoning pipeline directly in your terminal:

### A. Fail-Closed Test (Attempt dispatch without human sign-off):
```bash
python main.py run
```
You will observe:
1. Zetaris queries SCADA, DGA, and tickets in-place without data movement.
2. Nemotron causal reasoner evaluates rival hypotheses and refutes ungrounded theories.
3. Autonomous physical dispatch is **BLOCKED** by the `HumanApprovalGate` (Fail-closed invariant).

### B. Authorized Dispatch with Human Sign-off:
```bash
python main.py run --signoff --operator "Judge Evaluator"
```
You will observe:
1. Human sign-off token `HUMAN-SIGNOFF-<HASH>` issued.
2. Corrective switching order authorized and dispatched.
3. Cryptographic audit trail generated (`HG-GRIDMIND-ACK-<HASH>`).

---

## 4. Interactive Web Dashboard

Launch the local web dashboard:
```bash
python main.py web --port 8080
```
Open **[http://localhost:8080](http://localhost:8080)** in your browser (or double-click `web/index.html` directly).

Features available to judges:
- **Case Switcher:** Toggle across all 4 operational incidents in real-time.
- **Zetaris Federated Tables:** Inspect live row-level citations for SCADA telemetry and DGA oil tests.
- **Rival Hypothesis Falsification Panel:** Dynamic visual comparison of H1, H2, and H3 with probability deltas.
- **Human Approval Gate Simulator:** Test both the fail-closed rejection and the operator authorization flow.

---

## 5. Sponsor Technologies Audit

See [`docs/SPONSOR_EVALUATION.md`](SPONSOR_EVALUATION.md) for full technical disclosure:
- **Zetaris:** Virtual SQL Data Fabric schema and Lightning SQL query contracts.
- **Meterless:** Native H-MEM chronological memory, Markovian state transitions, and World Model invariants.
- **NVIDIA Nemotron:** Multi-step causal falsification engine with dual-mode (deterministic physical / live inference).
- **Cursor:** Development environment toolchain verification.

Zero incremental cost ($0.00 USD) guaranteed throughout development and evaluation.
