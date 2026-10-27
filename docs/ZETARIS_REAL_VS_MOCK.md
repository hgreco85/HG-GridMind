# Zetaris: real engine vs offline mock

Evidence date: 2026-10-27 (ART). Real engine: Zetaris 2.4.3.1 (driver image `...hackathon.cb88df0b`), local docker compose
on the author's Windows PC, UI/JDBC bound to loopback only. Cost: USD 0.

| Aspect | Mock (`zetaris_adapter.py`, default) | Real (`zetaris_real.py`, opt-in) |
|---|---|---|
| Execution | Returns the fixture rows; the SQL is only *printed* in the plan | SQL is executed by Zetaris Lightning (Spark) over JDBC |
| Table names | `zetaris_virtual.scada_telemetry`, `.maintenance_history`, `.tickets_database` (illustrative) | `gridmind_scada_pg.scada_telemetry` (PostgreSQL JDBC **datasource**), `gridmind_files.maintenance_history`, `gridmind_files.tickets_database` (CSV **Lightning filestore tables**) |
| Join semantics | Not executed (LEFT JOIN template text) | Executed: Postgres x CSV x CSV, inner joins, `verdict <> 'NORMAL'`, `neutral_current_amps > 15` |
| Data movement | Claimed zero-ETL (nothing moves because nothing is queried) | Zero-ETL for real: Postgres read in place via JDBC; CSVs read in place as filestore tables |
| `execution_mode` | `LOCAL_VIRTUAL_FEDERATION` (or `CLOUD`, decided by string-matching the endpoint) | `REAL_ZETARIS_ENGINE_LOCAL_DOCKER` |
| Rows | Fixture rows (e.g. incident 5501: 1 SCADA / 0 maint / 0 tickets) | Engine data for TR-102: 36 SCADA rows, 4 DGA rows, 4 tickets -> **10 joined rows** |
| Latency | ~0 ms | 1283 ms (JDBC run), 1125 ms in the UI; 345 ms warm via the bridge |
| Needs | Nothing | Docker stack + Java + jar + `ZETARIS_PASSWORD` |
| Failure | n/a | Never breaks GridMind: falls back to mock and records `reason` |

Honest limits
* The GridMind agent's reasoning still consumes the **fixtures**; the real-engine rows are additive, labelled evidence in
  `bundle["zetaris_real"]`. The real dataset only contains asset TR-102 (fixture `incident_INC_2026_UTIL_5501.json`); other
  fixtures (e.g. 8812 -> TR-404) legitimately return 0 real rows.
* Real engine data is synthetic (seed 5501), generated for this demo; it is not organizer data.
* Live test needs the engine; CI/offline runs skip it (`16 tests, 1 skipped`).

## Real queries and results (from `integrations/zetaris/evidence/`)
* `SELECT 1` -> 1 (165 ms); `SHOW SERVER VERSION` -> 2.4.3.1 / production.
* Q1 three-source federation for TR-102: 10 rows; e.g. SCADA-ROW-44012 (2026-10-23 01:50, neutral 37.5 A) + MNT-7002 (WATCH_HOT_SPOT, acetylene 4.8 ppm) + TKT-9001 / TKT-9002.
* Q2 fleet summary (3 assets): TR-102 max neutral 37.5 A, 2 tickets, acetylene 4.8; TR-205 5.5 A, 1, 0.1; TR-310 5.8 A, 1, 0.2.
