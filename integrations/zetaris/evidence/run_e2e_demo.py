"""End-to-end demo: HG GridMind + REAL Zetaris engine, with full traceability.

Runs the normal GridMind investigation (fixture-driven reasoning) while the adapter
executes the same federation on the authentic local Zetaris engine, then writes one
JSON trace containing: sources, executed SQL, engine rows, hypotheses, root cause,
approval gate and audit hash -- every claim linked to its origin (REAL vs SIMULATED).

Usage
-----
    python integrations/zetaris/evidence/run_e2e_demo.py \
        --fixture fixtures/incident_INC_2026_UTIL_5501.json \
        --out integrations/zetaris/evidence/06_e2e_trace.json --signoff
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from src.agent import GridMindCommander  # noqa: E402
from src.data_connector import FederatedDataConnector  # noqa: E402
from src.gate import HumanApprovalGate  # noqa: E402


def load_platform_env() -> None:
    if os.environ.get("ZETARIS_PASSWORD"):
        return
    env = Path(r"C:\Users\Administrator\hg-sandbox\zetaris\zetaris-platform\.env")
    if not env.is_file():
        return
    for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    os.environ.setdefault("ZETARIS_PASSWORD", os.environ.get("ZETARIS_ADMIN_PASSWORD", ""))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", default=str(REPO_ROOT / "fixtures" / "incident_INC_2026_UTIL_5501.json"))
    ap.add_argument("--out", default=str(Path(__file__).with_name("06_e2e_trace.json")))
    ap.add_argument("--signoff", action="store_true")
    ap.add_argument("--operator", default="Hernan Greco")
    ap.add_argument("--asset", default=None, help="asset id for the REAL engine query (defaults to the fixture asset)")
    args = ap.parse_args()

    load_platform_env()
    if args.asset:
        os.environ["GRIDMIND_ZETARIS_ASSET_ID"] = args.asset
    if os.environ.get("ZETARIS_JDBC_JAR") is None:
        jar = Path(r"C:\Users\Administrator\hg-sandbox\zetaris\zetaris-platform\jdbc\ndp-jdbc-driver-2.4.3.1-7eff043-driver.jar")
        if jar.is_file():
            os.environ["ZETARIS_JDBC_JAR"] = str(jar)
    os.environ["GRIDMIND_ZETARIS_REAL"] = "1"

    started_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    fixture = Path(args.fixture)
    asset = args.asset or "fixture asset"
    connector = FederatedDataConnector(fixture)
    gate = HumanApprovalGate()
    if args.signoff:
        gate = HumanApprovalGate.issue_token(
            operator_name=args.operator,
            operator_role="Lead Power Grid Dispatcher",
            action_summary="Feeder transfer and neutral terminal re-torque",
        )
    commander = GridMindCommander(connector, gate)
    diag = commander.investigate_incident()
    bundle_meta = diag.sponsor_metadata.get("zetaris", {})

    real = bundle_meta.get("real_engine_rows")
    real_used = not bundle_meta.get("federation_is_simulation")
    print("=" * 78)
    print("  HG GridMind x Zetaris - end-to-end trace")
    print("=" * 78)
    print(f"[0] Window   : started {started_utc}Z")
    print(f"    Fixture  : {fixture.name} (synthetic)")
    print(f"    Incident : {diag.incident_id} | Asset {diag.asset_id}")
    print(f"[1] Sources  : {bundle_meta.get('federation_engine')}")
    print("    - gridmind_scada_pg.scada_telemetry  (PostgreSQL datasource, zero-ETL)")
    print("    - gridmind_files.maintenance_history (CSV filestore table)")
    print("    - gridmind_files.tickets_database    (CSV filestore table)")
    print(f"    Real engine rows joined: {real} | asset queried: {asset} | simulation fallback: {not real_used}")
    print(f"[2] Engine   : {diag.sponsor_metadata.get('zetaris', {}).get('federation_engine')}")
    print("[3] Hypotheses and falsification:")
    for f in diag.falsified_hypotheses:
        print(f"    [X] FALSIFIED: {f['hypothesis']}")
        print(f"        ref: {f['falsified_by_citation']}")
    for idx, cit in enumerate(diag.evidence_trail, 1):
        mark = "SUPPORTS" if cit.supports_hypothesis else "REFUTES"
        print(f"    [{mark}] {cit.source_table}:{cit.row_id} -> {cit.fact_observed[:70]}")
    print(f"[4] Root cause: {diag.confirmed_root_cause}")
    print(f"[5] Action    : {diag.recommended_action}")
    print(f"[6] Gate      : approval_required={diag.approval_required} authorized={diag.is_authorized_by_human}")
    print(f"[7] Audit ACK : {diag.audit_ack_hash}")
    print("=" * 78)

    trace = {
        "trace_schema": "hg-gridmind/e2e-trace/1",
        "started_utc": started_utc,
        "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fixture": fixture.name,
        "incident_id": diag.incident_id,
        "asset_id": diag.asset_id,
        "engine_asset_queried": asset,
        "provenance": {
            "reasoning_rows": "fixtures (deterministic, synthetic)",
            "zetaris_evidence_rows": "REAL engine (gridmind_scada_pg + gridmind_files)",
            "real_engine_rows": real,
            "is_simulation_fallback": bundle_meta.get("federation_is_simulation"),
        },
        "sources": [
            {"name": "gridmind_scada_pg.scada_telemetry", "kind": "PostgreSQL JDBC datasource"},
            {"name": "gridmind_files.maintenance_history", "kind": "CSV Lightning filestore table"},
            {"name": "gridmind_files.tickets_database", "kind": "CSV Lightning filestore table"},
        ],
        "hypotheses": {
            "falsified": diag.falsified_hypotheses,
            "supported_citations": [
                {"source_table": c.source_table, "row_id": c.row_id, "fact": c.fact_observed}
                for c in diag.evidence_trail
            ],
        },
        "root_cause": diag.confirmed_root_cause,
        "recommended_action": diag.recommended_action,
        "gate": {"approval_required": diag.approval_required, "authorized": diag.is_authorized_by_human},
        "audit_ack": diag.audit_ack_hash,
        "sponsor_metadata": {k: v for k, v in diag.sponsor_metadata.items() if k != "cursor"},
        "real_engine_detail": connector.zetaris_fabric.execute_query_contract(
            "INCIDENT_FEDERATION", asset_id=args.asset or diag.asset_id
        ),
    }
    Path(args.out).write_text(json.dumps(trace, indent=2, default=str), encoding="utf-8")
    print(f"trace written: {args.out}")
    return 0 if real_used else 3


if __name__ == "__main__":
    raise SystemExit(main())
