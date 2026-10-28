# HG GridMind — Written explanation (Open Agent Hackathon 2026)

**Project:** HG GridMind, an auditable AI Incident Commander for power-grid trips (Challenge 02, *The Agent That Can Explain Why*; also entered for the Zetaris demo and the Wildcard track).
**Author:** Hernán Francisco Greco (`@hgreco85`), team HG Stack. **Repo:** https://github.com/hgreco85/HG-GridMind · **Live demo:** https://hgreco85.github.io/HG-GridMind/
**Spend:** USD 0.00. No API keys, no paid services. All data is synthetic.

## 1. What it does

When a distribution transformer trips, operators tend to assume the worst (internal insulation failure, USD 250k+ replacement). GridMind investigates instead: it pulls evidence from fragmented silos (SCADA telemetry, maintenance and dissolved-gas history, outage tickets), builds competing hypotheses, tries to *falsify* each against physical sensor data, abstains when evidence is missing, and answers **why** with row-level citations. Remediation stays locked behind a fail-closed human approval gate (`HumanApprovalGate`). A 24-case benchmark (4 anchor topologies + 20 parametric variations) checks it is not overfitted.

## 2. Zetaris integration

**What was built.** `src/sponsors/zetaris_real.py` connects GridMind to a **real Zetaris platform 2.4.3.1** (7-container docker compose stack: Postgres, Spark-based Lightning driver, API, UI, bootstrap) through the official JDBC driver. Federation uses Lightning SQL: a PostgreSQL datasource (`CREATE DATASOURCE`, `REGISTER DATASOURCE TABLES`) plus two CSV filestore tables (`CREATE LIGHTNING FILESTORE TABLE`), joined **in place without ETL**:

`scada_telemetry` (PostgreSQL) ⨝ `maintenance_history` (CSV) ⨝ `tickets_database` (CSV), filtered on neutral current > 15 A.

**Evidence it is real, not simulated.** `integrations/zetaris/evidence/` holds the JDBC results (federated join: 10 rows, 0.6–1.3 s), `docker ps`, versions and bootstrap logs. `docs/evidence/zetaris/` has real screenshots of the Zetaris UI (federated tree, the query typed in the SQL workspace, "Success" with total count 10) and a 1080p screen recording. The live test (`tests/test_zetaris_real.py`) runs against the engine and passes.

**How it is wired.** `FederatedDataConnector` is opt-in (`GRIDMIND_ZETARIS_REAL=1`). It adds `result["zetaris_real"]` with the real rows, and never raises: if the engine is unreachable it reports `{"used": false, "fallback": "MOCK"}` and the deterministic offline pipeline continues. The password only travels as an environment variable. Details and an honest real-vs-mock table: `docs/ZETARIS_REAL_VS_MOCK.md`.

**Limits.** The real engine holds a small synthetic dataset covering one asset (TR-102, fixture 5501); other fixtures still use the offline mock. The stack runs locally, not in a hosted Zetaris cloud.

## 3. Meterless integration

**Finding.** Meterless engines are open source (Apache-2.0) specifications with reference implementations; they need **no API key or credits**, so the genuine integration is to run the real engine.

**What was built.** `src/sponsors/meterless_real.py` and `integrations/meterless/` run the **real Meterless H-MEM reference engine** (`Meterless/Meterless@1742dec`, `engines/hmem/reference`, vendored by `setup.sh`). Each real Zetaris row becomes an H-MEM memory with provenance (`zetaris:<datasource>/<row_id>`). GridMind then asks questions ("why is the neutral overloaded on TR-102", "what does the DGA say", "which tickets relate"), and H-MEM returns its own hybrid-ranked memories, retrieval trace and **TrustLedger** history (create, read, feedback). Operator feedback adjusts confidence using the engine's own deltas. Memory persists between runs, so a later incident recalls earlier evidence without re-querying.

**Evidence.** `integrations/meterless/evidence/live_chain_zetaris_to_hmem.json` (real Zetaris → real H-MEM: 8 memories, 3 ranked recalls with sources and ledger), `tests_live.txt` (23/23 tests with both engines live, none skipped), and the upstream engine's own 10 tests passing.

**Honest limits.** Only H-MEM runs for real. The World Model, Markovian and Scout Intent engines are still represented by the pre-existing local Python mimic (`meterless_adapter.py`, which is a re-implementation, not Meterless code). The reference engine ranks with deterministic hash embeddings, so relevance scores are modest (about 0.33–0.36).

## 4. How Cursor was used

Cursor is the technical executor in the author's workflow: tasks are written as GitHub issues (#8 and #9 are the canonical specs for the Zetaris work), implemented by an AI coding agent on a branch, verified by running the test suite, and delivered as a Draft pull request (#10) for human review. For the real-engine work the agent wrote the two bridges, their tests and the evidence scripts (PR #10); every change is traceable in the git history (`edef57c` … `d974e6f`) and the PR. Nothing was merged to `main` or submitted without the author's approval.

## 5. NVIDIA

NVIDIA Nemotron is represented by `nemotron_adapter.py`, a **deterministic physics-rules reasoner** (dissolved-gas thresholds, current symmetry, thermal checks) that produces the hypotheses and falsification. The code includes an OpenAI-compatible / NIM connector, but **no live Nemotron inference was run for this submission**, so no claim of live Nemotron calls is made.

## 6. What is new vs pre-existing

First working version: commits of 2026-10-23 (agent, gate, deterministic adapters, fixtures, web demo, benchmark, docs). New on 2026-10-27 (PR #10): both real-engine bridges, `integrations/`, their tests and evidence, the README and this document. See README section 2c for the file-level declaration.

## 7. Reproduce

```bash
python main.py test && python evaluator.py          # offline, zero setup
bash integrations/meterless/setup.sh                # real H-MEM (free)
# real Zetaris: see integrations/zetaris/README.md (docker compose + JDBC jar; secrets via env vars)
GRIDMIND_ZETARIS_REAL=1 GRIDMIND_METERLESS_REAL=1 python integrations/meterless/demo_live_chain.py out.json
```
