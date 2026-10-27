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
| `evidence/` | verify.sh output, versions, `docker ps`, query results + timings, UI capture script |
| `../../src/sponsors/zetaris_real.py` | Python bridge (subprocess to the JDBC helper) |
| `../../docs/evidence/zetaris/` | UI screenshots + 1080p recording of the query running in the Zetaris UI |

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
With nothing set, GridMind runs exactly as before (mock). If the engine is requested but unreachable,
`bundle["zetaris_real"] == {"used": False, "fallback": "MOCK", "reason": ...}`; the pipeline never breaks.

See `docs/ZETARIS_REAL_VS_MOCK.md` for the real-vs-mock differences.
