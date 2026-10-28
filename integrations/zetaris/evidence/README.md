# Evidence index — real Zetaris engine (HG GridMind)

Engine: **Zetaris 2.4.3.1**, build `cb88df0b`, local `docker compose` (project `zetaris`), JDBC on
`127.0.0.1:10000`. Cost: **USD 0** (official hackathon images already on the machine; no AWS, no cloud spend).
Data: **synthetic** (seed 5501). No secret is stored in any file here.

| File | What it proves | When (UTC) |
|---|---|---|
| `05_live_verified.json` | Fresh timestamped run: engine version/build, container IDs + health, `SHOW DATASOURCES` / `SHOW LIGHTNING TABLES`, the 3-source federated query (10 rows) and the fleet summary (3 assets), per-statement latency, driver-jar SHA-256 | 2026-10-28 14:54 |
| `06_e2e_trace_TR102.json` | GridMind E2E on fixture `INC-2026-UTIL-5501` (asset TR-102) with the real engine: 10 engine rows, sources, hypotheses, gate, audit ACK | 2026-10-28 14:55 |
| `07_e2e_trace_INC8812.json` | GridMind E2E headline case `INC-2026-UTIL-8812` (TR-404) with the real engine evidence block (10 rows for TR-102, labelled): 2 hypotheses falsified, 2 supported citations, root cause, remediation, audit ACK | 2026-10-28 14:56 |
| `01_smoke.json` … `04_federated.json` | First light of the engine (2026-10-27): `SELECT 1`, setup, probe, federated joins | 2026-10-27 |
| `verify.txt`, `versions.txt`, `docker_ps.txt`, `log_*.txt` | `verify.sh` 9/9 PASS, image digests, container list, bootstrap/api/driver logs | 2026-10-27 |
| `../docs/evidence/zetaris/zetaris_ui_live_20261028T145726Z.webm` | 1080p screen recording of the **Zetaris UI** running the federated SQL: `Success · Total Count: 10 · Query Time: 1.456 s` | 2026-10-28 14:57 |
| `../docs/evidence/zetaris/ui_live_20261028T145726Z_*.png` | Keyframes of that session (login masked, catalog tree, SQL, results grid) | 2026-10-28 14:57 |
| `../docs/evidence/zetaris/gridmind_e2e_transcript_20261028T145846Z.webm` | Clip of the E2E trace (rendered from `07_e2e_trace_INC8812.json`, not re-run) | 2026-10-28 14:58 |

## Reproduce

```bash
# 1. engine up (existing containers; no recreation, volumes kept)
powershell -File scripts/zetaris/zetaris_on.ps1

# 2. fresh timestamped evidence
python integrations/zetaris/evidence/run_live_evidence.py \
  --jar /path/to/ndp-jdbc-driver-2.4.3.1-*-driver.jar \
  --out integrations/zetaris/evidence/05_live_verified.json --show-summary

# 3. end-to-end GridMind with the real engine
python integrations/zetaris/evidence/run_e2e_demo.py \
  --fixture fixtures/incident_INC_2026_UTIL_8812.json --asset TR-102 --signoff \
  --out integrations/zetaris/evidence/07_e2e_trace_INC8812.json

# 4. screen recording of the UI (needs Playwright + its ffmpeg: python -m playwright install ffmpeg)
python integrations/zetaris/evidence/capture_ui_video.py

# 5. engine off again (keeps volumes)
powershell -File scripts/zetaris/zetaris_off.ps1
```

`run_live_evidence.py` writes `verdict.real_engine_contacted=true` **only** after the engine answered;
if anything is missing it exits non-zero and writes the exact blocker instead.
