# Zetaris: real engine vs simulation fallback

Last verified: **2026-10-28 (UTC)** — engine `Zetaris 2.4.3.1`, build `cb88df0b`, local `docker compose`
(project `zetaris`), JDBC bound to loopback. Cost: **USD 0**. Evidence:
`integrations/zetaris/evidence/05_live_verified.json` (timestamps, containers, SQL, rows, latencies).

## How the code is organised

`src/sponsors/zetaris_adapter.py` is the single entry point and exposes **two labelled paths**:

| Method | Path | What happens |
|---|---|---|
| `execute_query_contract()` | **REAL** (opt-in) | Executes the contract's SQL on the authentic engine through `src/sponsors/zetaris_real.py` (official JDBC driver, `ZETARIS_PASSWORD` via env only). Returns `execution_mode = REAL_ZETARIS_ENGINE_LOCAL_DOCKER`, `is_simulation = false`, plus rows/columns/latency from the engine. |
| `execute_query_contract()` when the engine is off/unconfigured | **SIMULATION fallback** | Returns `used = false`, `fallback = "SIMULATION"`, `is_simulation = true` and the exact reason. Never raises. |
| `execute_virtual_query()` | **SIMULATION** (always) | Replays the incident fixture rows and reports the plan. Every result carries `is_simulation: true` + `simulation_disclosure`; the plan says `engine: "SIMULATED (no engine contacted)"` and `zero_etl_guaranteed: false`. |

`src/data_connector.py` now delegates the real query to the adapter (no second code path) and labels the
bundle: `metadata.federation_engine` is *"Zetaris Lightning (REAL, local docker compose)"* or
*"SIMULATED federation (fixture replay, no engine contacted)"*, with `federation_is_simulation` and
`real_engine_rows`.

## Real vs simulated, side by side

| Aspect | SIMULATION | REAL |
|---|---|---|
| Trigger | default (`execute_virtual_query`) | `GRIDMIND_ZETARIS_REAL=1` + `ZETARIS_JDBC_JAR` + `ZETARIS_PASSWORD` + `java` |
| Execution | none: fixture rows are replayed | Zetaris Lightning (Spark) over JDBC |
| Table names | illustrative `zetaris_virtual.*` in the documented template | `gridmind_scada_pg.scada_telemetry` (PostgreSQL JDBC datasource), `gridmind_files.maintenance_history`, `gridmind_files.tickets_database` (CSV Lightning filestore tables) |
| Join semantics | not executed | executed: Postgres × CSV × CSV, inner joins, `verdict <> 'NORMAL'`, `neutral_current_amps > 15` |
| Data movement | n/a | zero-ETL: Postgres read in place, CSVs read in place |
| Rows | fixture rows (e.g. incident 5501: 1 SCADA / 0 maint / 0 tickets) | TR-102: 36 SCADA rows, 4 DGA rows, 4 tickets -> **10 joined rows** |
| Latency | ~0 ms | 4.1 s cold JDBC join; 1.46 s in the UI; 0.7–1.3 s warm |
| Failure mode | n/a | falls back to SIMULATION with the reason recorded; pipeline never breaks |
| Disclosure in payload | `is_simulation: true`, `simulation_disclosure` | `is_simulation: false`, `execution_mode`, `engine_status` |

## Verified real queries (2026-10-28)

* `SHOW SERVER VERSION` -> `2.4.3.1` / `production` / build `cb88df0b`.
* Inventory: 1 datasource (`gridmind_scada_pg`), 3 Lightning databases, `gridmind_files` with
  `maintenance_history` + `tickets_database`.
* Q1 three-source federation for TR-102: **10 rows**; e.g. `SCADA-ROW-44012` (2026-10-23 01:50, neutral
  37.5 A) + `MNT-7002` (`WATCH_HOT_SPOT`, acetylene 4.8 ppm) + `TKT-9001` / `TKT-9002`.
* Q2 fleet summary: TR-102 max neutral 37.5 A, 2 tickets, acetylene 4.8; TR-205 5.5 A, 1, 0.1; TR-310 5.8 A, 1, 0.2.
* UI: `Success · Total Count: 10 · Query Time: 1.456 s` (`docs/evidence/zetaris/zetaris_ui_live_20261028T145726Z.webm`).

## Honest limits

* The GridMind agent's reasoning still consumes the **fixtures**; the real-engine rows are additive,
  labelled evidence in `bundle["zetaris_real"]`. The engine's synthetic dataset covers asset TR-102 only
  (fixture `INC-2026-UTIL-5501`); other fixtures legitimately return 0 real rows.
* The engine data is synthetic (seed 5501), generated for this demo; it is not organiser data.
* Live tests need the engine; offline runs skip them (`25 tests, 4 skipped`).
