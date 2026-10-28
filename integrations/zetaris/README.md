# Real Zetaris engine for HG GridMind (opt-in, USD 0, local only)

This folder wires GridMind to a **real** Zetaris platform (2.4.3.1, docker compose, JDBC) while
keeping the deterministic offline mock (`src/sponsors/zetaris_adapter.py`) as the default and as the
automatic fallback. Everything here uses **synthetic, non-confidential** data (seed 5501).

## Layout
| Path | What |
|---|---|
| `data/` | Synthetic SCADA (PostgreSQL seed SQL + CSV), maintenance/DGA CSV, tickets CSV |
| `docker-compose.override.yml` | Adds a demo PostgreSQL next to the Zetaris stack; binds the UI to `127.0.0.1` only |
| `sql/02_setup.sql` | `CREATE DATASOURCE` (PostgreSQL) + `CREATE LIGHTNING DATABASE/FILESTORE TABLE` (CSV) |
| `sql/04_federated.sql` | The real 3-source federated queries |
| `runner/ZetarisJdbcRunner.java` | Single-file JDBC helper (password via env var only) |
| `evidence/` | Timestamped live runs (`05_live_verified.json`, `06`/`07` E2E traces), verify.sh output, versions, `docker ps`, query results + timings, UI capture scripts |
| `evidence/run_live_evidence.py` | One-shot, timestamped evidence: engine version/build, containers, SQL, rows, latencies, full JSON |
| `evidence/run_e2e_demo.py` | GridMind E2E against the real engine with a provenance trace (sources, rows, hypotheses, gate, ACK) |
| `evidence/capture_ui_video.py` | 1080p screen recording of the real Zetaris UI running the federated SQL |
| `evidence/render_transcript_clip.py` | Renders a recorded E2E trace as a video clip (no re-run) |
| `../../src/sponsors/zetaris_adapter.py` | Real-first facade: `execute_query_contract()` (REAL) + `execute_virtual_query()` (labelled SIMULATION) |
| `../../src/sponsors/zetaris_real.py` | Python bridge (subprocess to the JDBC helper) |
| `../../docs/evidence/zetaris/` | UI screenshots + 1080p recordings of the query running in the Zetaris UI |
| `../../docs/ZETARIS_VIDEO_AUTHENTIC_SCENES.md` | Which authentic clip replaces which conceptual scene in the demo video |

## Reproduce (Windows or Linux with Docker, Java 11+)
1. Get the Zetaris bundle and registry credentials from the organizers; `docker login` to their registry.
2. `docker compose -f docker-compose.yml -f integrations/zetaris/docker-compose.override.yml up -d`
   (copy `data/01_scada_pg.sql` to `demo-data/` and the two CSVs into the driver's
   `/home/zetaris/customer-data/shared/gridmind/`), then `./verify.sh` -> 9/9 PASS.
3. Run `sql/02_setup.sql` through the runner (registers the datasource and file tables).
4. Use GridMind against the engine:
```bash
export ZETARIS_JDBC_JAR=/path/to/ndp-jdbc-driver-2.4.3.1-*-driver.jar
export ZETARIS_PASSWORD=...            # never commit / never pass on argv
export GRIDMIND_ZETARIS_REAL=1         # opt-in
python -m unittest discover tests      # + set GRIDMIND_ZETARIS_LIVE=1 to run the live test
```
With nothing set, GridMind runs exactly as before (simulation). If the engine is requested but unreachable,
`bundle["zetaris_real"] == {"used": False, "fallback": "SIMULATION", "is_simulation": True, "reason": ...}`; the
pipeline never breaks.

## Latest verified run (2026-10-28, UTC)

| Item | Value |
|---|---|
| Engine | Zetaris 2.4.3.1, build `cb88df0b`, local docker compose |
| Federated query | Postgres `gridmind_scada_pg.scada_telemetry` × CSV `maintenance_history` × CSV `tickets_database` |
| Result | 10 joined rows for TR-102; fleet summary for TR-102 / TR-205 / TR-310 |
| Latency | 4.1 s (JDBC cold), 1.456 s (UI), ~0.7–1.3 s warm |
| Evidence | `evidence/05_live_verified.json`, `evidence/06_e2e_trace_TR102.json`, `evidence/07_e2e_trace_INC8812.json`, `../../docs/evidence/zetaris/zetaris_ui_live_20261028T145726Z.webm` |
| Tests | `25 tests, 3 skipped` offline; with `GRIDMIND_ZETARIS_LIVE=1` the live JDBC test passes (`evidence/tests_live_20261028.txt`) |

See `docs/ZETARIS_REAL_VS_MOCK.md` for the real-vs-mock differences.
