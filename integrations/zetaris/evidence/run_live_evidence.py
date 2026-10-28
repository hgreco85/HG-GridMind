"""Live, timestamped evidence run against a REAL local Zetaris engine.

Reproducible: it talks to the same stack the bridge uses (docker compose project
``zetaris``, JDBC on 127.0.0.1:10000) and writes one JSON file with engine identity,
container state, the exact SQL, the rows the engine returned, timings and timestamps.

No secret is written: the JDBC password is read from ``ZETARIS_PASSWORD`` (or the
platform ``.env``) and never serialised. ``--show-summary`` prints a short human
summary instead of the full JSON.

Usage
-----
    python integrations/zetaris/evidence/run_live_evidence.py \
        --jar "C:/.../ndp-jdbc-driver-2.4.3.1-*-driver.jar" \
        --out integrations/zetaris/evidence/05_live_verified.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from src.sponsors.zetaris_real import REAL_EXECUTION_MODE, ZetarisRealEngine  # noqa: E402

ENV_CANDIDATES = [
    Path(r"C:\Users\Administrator\hg-sandbox\zetaris\zetaris-platform\.env"),
    REPO_ROOT / "integrations" / "zetaris" / ".env",
]

INVENTORY_SQL = """
SHOW SERVER VERSION;
SHOW DATASOURCES;
SHOW LIGHTNING DATABASES;
SHOW DATASOURCE TABLES gridmind_scada_pg;
SHOW LIGHTNING TABLES gridmind_files;
""".strip()

FEDERATION_SQL = """
SELECT s.row_id AS scada_row_id, s.ts, s.current_phase_b_amps, s.neutral_current_amps,
       m.row_id AS maint_row_id, m.verdict AS dga_verdict, m.acetylene_ppm,
       t.row_id AS ticket_row_id, t.ticket_type, t.reported_at
FROM gridmind_scada_pg.scada_telemetry s
JOIN gridmind_files.maintenance_history m ON m.asset_id = s.asset_id AND m.verdict <> 'NORMAL'
JOIN gridmind_files.tickets_database t ON t.affected_feeder = s.feeder_id
WHERE s.asset_id = 'TR-102' AND s.neutral_current_amps > 15
ORDER BY s.ts DESC, t.row_id;
""".strip()

FLEET_SQL = """
SELECT s.asset_id, MAX(s.neutral_current_amps) AS max_neutral_a,
       COUNT(DISTINCT t.row_id) AS open_tickets, MAX(m.acetylene_ppm) AS max_acetylene_ppm
FROM gridmind_scada_pg.scada_telemetry s
LEFT JOIN gridmind_files.maintenance_history m ON m.asset_id = s.asset_id
LEFT JOIN gridmind_files.tickets_database t ON t.affected_feeder = s.feeder_id
GROUP BY s.asset_id
ORDER BY s.asset_id;
""".strip()


def now_pair() -> tuple[str, str]:
    utc = datetime.now(timezone.utc)
    return utc.isoformat(timespec="seconds"), utc.astimezone().isoformat(timespec="seconds")


def load_env() -> Path | None:
    """Loads the platform .env into os.environ (first file that exists). Never printed."""
    if os.environ.get("ZETARIS_PASSWORD"):
        return None
    for candidate in ENV_CANDIDATES:
        if not candidate.is_file():
            continue
        for line in candidate.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
        os.environ.setdefault("ZETARIS_PASSWORD", os.environ.get("ZETARIS_ADMIN_PASSWORD", ""))
        return candidate
    return None


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def docker_containers() -> list[dict]:
    try:
        out = subprocess.run(
            ["docker", "ps", "-a", "--filter", "name=zetaris-",
             "--format", "{{.Names}}\t{{.Image}}\t{{.Status}}"],
            capture_output=True, text=True, timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    rows = []
    for line in out.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        ident = None
        try:
            insp = subprocess.run(
                ["docker", "inspect", parts[0], "--format",
                 "{{.Id}}|{{.Image}}|{{.State.Health.Status}}"],
                capture_output=True, text=True, timeout=60,
            )
            ident = insp.stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            pass
        rows.append({"name": parts[0], "image": parts[1], "status": parts[2], "inspect": ident})
    return rows


def java_version() -> str:
    try:
        out = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=60)
        return (out.stderr or out.stdout).strip().splitlines()[0]
    except (OSError, subprocess.TimeoutExpired, IndexError):
        return "unavailable"


def build_section(engine: ZetarisRealEngine, name: str, sql: str) -> list[dict]:
    section = []
    for st in engine.run_sql(sql):
        section.append(
            {
                "name": name,
                "sql": st["sql"],
                "columns": st.get("columns", []),
                "row_count": len(st.get("rows", [])),
                "rows": st.get("rows", []),
                "elapsed_ms": st.get("elapsed_ms"),
            }
        )
    return section


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jar", default=os.environ.get("ZETARIS_JDBC_JAR", ""))
    ap.add_argument("--jdbc-url", default=os.environ.get("ZETARIS_JDBC_URL", ""))
    ap.add_argument("--out", default=str(Path(__file__).with_name("05_live_verified.json")))
    ap.add_argument("--show-summary", action="store_true")
    args = ap.parse_args()

    env_file = load_env()
    if args.jar:
        os.environ["ZETARIS_JDBC_JAR"] = args.jar
    engine = ZetarisRealEngine(jdbc_url=args.jdbc_url or None)

    started_utc, started_local = now_pair()
    report: dict = {
        "evidence_schema": "hg-gridmind/zetaris-live-evidence/1",
        "started_utc": started_utc,
        "started_local": started_local,
        "host": {"platform": platform.platform(), "machine": platform.machine(), "python": platform.python_version()},
        "java": java_version(),
        "env_file_used": str(env_file) if env_file else "(env already populated)",
        "jdbc_url": engine.jdbc_url,
        "execution_mode": REAL_EXECUTION_MODE,
        "driver_jar": {"path": engine.jar_path, "sha256": sha256(engine.jar_path) if engine.jar_path and Path(engine.jar_path).is_file() else None},
        "containers": docker_containers(),
        "statements": [],
        "verdict": {},
    }

    problem = engine.configuration_problem()
    if problem:
        report["verdict"] = {"real_engine_contacted": False, "sql_executed": False, "reason": problem}
        finished_utc, finished_local = now_pair()
        report["finished_utc"], report["finished_local"] = finished_utc, finished_local
        Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"BLOCKED: {problem} -> {args.out}")
        return 2

    try:
        report["statements"] += build_section(engine, "inventory", INVENTORY_SQL)
        report["statements"] += build_section(engine, "incident_federation_TR-102", FEDERATION_SQL)
        report["statements"] += build_section(engine, "fleet_summary", FLEET_SQL)
    except Exception as exc:  # noqa: BLE001 - evidence run must record, not crash
        report["verdict"] = {"real_engine_contacted": True, "sql_executed": False, "reason": str(exc)[:400]}
        finished_utc, finished_local = now_pair()
        report["finished_utc"], report["finished_local"] = finished_utc, finished_local
        Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"ERROR: {exc} -> {args.out}")
        return 1

    version_rows = next((s["rows"] for s in report["statements"] if s["sql"].strip().upper().startswith("SHOW SERVER VERSION")), [])
    federation = next(s for s in report["statements"] if s["name"] == "incident_federation_TR-102")
    fleet = next(s for s in report["statements"] if s["name"] == "fleet_summary")
    finished_utc, finished_local = now_pair()
    report["finished_utc"], report["finished_local"] = finished_utc, finished_local
    report["verdict"] = {
        "real_engine_contacted": True,
        "sql_executed": True,
        "engine_version": version_rows[0][0] if version_rows else None,
        "engine_build_hash": version_rows[0][4] if version_rows and len(version_rows[0]) > 4 else None,
        "federation_rows": federation["row_count"],
        "federation_sources_joined": sorted({c for c in federation["columns"] if c.endswith("_row_id")}),
        "fleet_assets": [r[0] for r in fleet["rows"]],
        "total_elapsed_ms": sum((s.get("elapsed_ms") or 0) for s in report["statements"]),
        "cost_usd": 0.0,
        "password_in_report": False,
    }
    Path(args.out).write_text(json.dumps(report, indent=2), encoding="utf-8")

    if args.show_summary:
        v = report["verdict"]
        print(f"evidence      : {args.out}")
        print(f"window (UTC)  : {report['started_utc']} -> {report['finished_utc']}")
        print(f"engine        : Zetaris {v['engine_version']} build {v['engine_build_hash']} via JDBC")
        print(f"federated rows: {v['federation_rows']} ({', '.join(v['federation_sources_joined'])})")
        print(f"fleet assets  : {', '.join(v['fleet_assets'])}")
        print(f"elapsed total : {v['total_elapsed_ms']} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
