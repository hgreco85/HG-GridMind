# Meterless H-MEM integration (real engine, free, no API key)

Meterless engines are open source (Apache-2.0) specs + reference implementations; there is no API key,
account or credit system. This integration **runs the real Meterless H-MEM reference engine**
(`Meterless/Meterless@1742dec`, `engines/hmem/reference`) and wires it to GridMind's real Zetaris results.

```bash
bash integrations/meterless/setup.sh          # node>=18, npm, git. Vendors H-MEM into vendor/ (gitignored)
export GRIDMIND_ZETARIS_REAL=1 GRIDMIND_METERLESS_REAL=1   # both opt-in; Zetaris env vars: see ../zetaris/README.md
python integrations/meterless/demo_live_chain.py out.json
python -m unittest discover tests             # engine tests auto-skip when H-MEM is not vendored
```

Flow: `Zetaris Lightning federated join (real rows)` -> `gridmind_hmem.ts` writes one H-MEM memory per source row
(provenance `zetaris:<datasource>/<row_id>`, confidence 0.9) -> GridMind asks questions -> H-MEM's own hybrid
ranking (AGENTS.md 6.1) returns memories + retrieval trace -> optional operator feedback (+0.05 / -0.03 / -0.2) ->
TrustLedger history per memory (create / read / feedback). State persists in `.state/` (gitignored), so later
incidents recall earlier ones without re-querying.

Evidence (`evidence/`): `live_chain_zetaris_to_hmem.json` (real Zetaris -> real H-MEM on the author's PC),
`tests_live.txt` (23 tests, 0 skipped), `upstream_hmem_conformance_smoke.txt` (upstream engine's own 10 tests).

Honest limits: only H-MEM is run for real. World Model, Markovian and Scout Intent are still the pre-existing local
Python mimic in `src/sponsors/meterless_adapter.py`. The reference engine's retrieval is deterministic hash-embedding
based (not an LLM). Relevance scores are therefore modest (~0.33-0.36); GridMind queries use threshold 0.1 and top-5.
