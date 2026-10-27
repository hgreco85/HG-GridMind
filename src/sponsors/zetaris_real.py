"""Opt-in bridge from HG GridMind to a REAL Zetaris Lightning engine (JDBC).

This module does NOT replace the offline mock in ``zetaris_adapter.py``. It adds a
second, explicitly-labelled execution path that talks to a locally running
Zetaris platform (docker compose, v2.4.3.1) through the official JDBC driver.

Design rules
------------
* Opt-in only: nothing happens unless ZETARIS_JDBC_JAR and ZETARIS_PASSWORD are set
  (and ``java`` is on PATH, and the engine answers).
* No secrets in code, argv, or logs: the password is passed to the JDBC helper via
  the ``ZETARIS_PASSWORD`` environment variable only.
* Any failure raises ``ZetarisRealEngineUnavailable``; callers fall back to the mock
  and must label the result as such (``execution_mode``).
* Stdlib only (subprocess + json). The JDBC helper is a single-file Java program
  (``integrations/zetaris/runner/ZetarisJdbcRunner.java``).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RUNNER = REPO_ROOT / "integrations" / "zetaris" / "runner" / "ZetarisJdbcRunner.java"
DEFAULT_JDBC_URL = "jdbc:zetaris:lightning@localhost:10000"
DEFAULT_USER = "admin@zetaris.com"
REAL_EXECUTION_MODE = "REAL_ZETARIS_ENGINE_LOCAL_DOCKER"

# Real table names as registered by integrations/zetaris/sql/02_setup.sql
INCIDENT_FEDERATION_SQL = """
SELECT s.row_id AS scada_row_id, s.ts, s.current_phase_b_amps, s.neutral_current_amps,
       m.row_id AS maint_row_id, m.verdict AS dga_verdict, m.acetylene_ppm,
       t.row_id AS ticket_row_id, t.ticket_type, t.reported_at
FROM gridmind_scada_pg.scada_telemetry s
JOIN gridmind_files.maintenance_history m ON m.asset_id = s.asset_id AND m.verdict <> 'NORMAL'
JOIN gridmind_files.tickets_database t ON t.affected_feeder = s.feeder_id
WHERE s.asset_id = '{asset_id}' AND s.neutral_current_amps > {neutral_threshold}
ORDER BY s.ts DESC, t.row_id
""".strip()

FLEET_SUMMARY_SQL = """
SELECT s.asset_id, MAX(s.neutral_current_amps) AS max_neutral_a,
       COUNT(DISTINCT t.row_id) AS open_tickets, MAX(m.acetylene_ppm) AS max_acetylene_ppm
FROM gridmind_scada_pg.scada_telemetry s
LEFT JOIN gridmind_files.maintenance_history m ON m.asset_id = s.asset_id
LEFT JOIN gridmind_files.tickets_database t ON t.affected_feeder = s.feeder_id
GROUP BY s.asset_id
ORDER BY s.asset_id
""".strip()

_ASSET_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")


class ZetarisRealEngineUnavailable(RuntimeError):
    """Raised when the real engine is not configured, not reachable, or errors."""


class ZetarisRealEngine:
    """Runs Lightning SQL on a real Zetaris engine via the JDBC helper."""

    def __init__(
        self,
        jdbc_url: Optional[str] = None,
        jar_path: Optional[str] = None,
        user: Optional[str] = None,
        runner_path: Optional[Path] = None,
        timeout_s: int = 180,
    ):
        self.jdbc_url = jdbc_url or os.environ.get("ZETARIS_JDBC_URL", DEFAULT_JDBC_URL)
        self.jar_path = jar_path or os.environ.get("ZETARIS_JDBC_JAR", "")
        self.user = user or os.environ.get("ZETARIS_USER", DEFAULT_USER)
        self.runner_path = Path(runner_path or DEFAULT_RUNNER)
        self.timeout_s = timeout_s

    # -- configuration -----------------------------------------------------
    def configuration_problem(self) -> Optional[str]:
        """Returns a human-readable reason if the engine cannot be used, else None."""
        if not self.jar_path or not Path(self.jar_path).is_file():
            return "ZETARIS_JDBC_JAR is not set or the jar does not exist"
        if not os.environ.get("ZETARIS_PASSWORD"):
            return "ZETARIS_PASSWORD is not set"
        if shutil.which("java") is None:
            return "java is not on PATH"
        if not self.runner_path.is_file():
            return f"JDBC runner not found: {self.runner_path}"
        return None

    def is_configured(self) -> bool:
        return self.configuration_problem() is None

    # -- execution ---------------------------------------------------------
    def run_sql(self, sql: str) -> List[Dict[str, Any]]:
        """Runs one or more ';'-terminated statements; returns the runner's statement list."""
        problem = self.configuration_problem()
        if problem:
            raise ZetarisRealEngineUnavailable(problem)
        sql_text = sql.strip()
        if not sql_text.endswith(";"):
            sql_text += ";"
        cmd = ["java", "-cp", self.jar_path, str(self.runner_path), self.jdbc_url, self.user, "-"]
        try:
            proc = subprocess.run(
                cmd,
                input=sql_text.encode("utf-8"),
                capture_output=True,
                timeout=self.timeout_s,
                env=os.environ.copy(),  # carries ZETARIS_PASSWORD; never placed in argv
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ZetarisRealEngineUnavailable(f"JDBC runner failed to run: {type(exc).__name__}") from exc
        stdout = proc.stdout.decode("utf-8", "replace").strip()
        if proc.returncode != 0 or not stdout.startswith("{"):
            tail = proc.stderr.decode("utf-8", "replace").strip().splitlines()[-1:]  # last line only
            raise ZetarisRealEngineUnavailable(
                f"engine not reachable (exit {proc.returncode}): {tail[0][:200] if tail else 'no output'}"
            )
        try:
            statements = json.loads(stdout)["statements"]
        except (ValueError, KeyError) as exc:
            raise ZetarisRealEngineUnavailable("unparseable runner output") from exc
        for st in statements:
            if "error" in st:
                raise ZetarisRealEngineUnavailable(f"engine rejected statement: {st['error'][:200]}")
        return statements

    def query(self, sql: str) -> Dict[str, Any]:
        st = self.run_sql(sql)[0]
        cols = st.get("columns", [])
        rows = [dict(zip(cols, r)) for r in st.get("rows", [])]
        return {"sql": st["sql"], "columns": cols, "rows": rows, "row_count": len(rows), "elapsed_ms": st.get("elapsed_ms")}

    # -- GridMind queries ---------------------------------------------------
    def incident_federation(self, asset_id: str, neutral_threshold: float = 15.0) -> Dict[str, Any]:
        """Three-source join (PostgreSQL datasource + 2 CSV filestore tables) for one asset."""
        if not _ASSET_RE.match(asset_id):
            raise ValueError("asset_id must match [A-Za-z0-9_.-]{1,64}")
        sql = INCIDENT_FEDERATION_SQL.format(asset_id=asset_id, neutral_threshold=float(neutral_threshold))
        res = self.query(sql)
        res.update(
            {
                "execution_mode": REAL_EXECUTION_MODE,
                "engine": "Zetaris Lightning (real, docker compose)",
                "sources": ["gridmind_scada_pg (PostgreSQL JDBC datasource)",
                            "gridmind_files.maintenance_history (CSV filestore)",
                            "gridmind_files.tickets_database (CSV filestore)"],
                "data_movement_required": False,
            }
        )
        return res

    def fleet_summary(self) -> Dict[str, Any]:
        res = self.query(FLEET_SUMMARY_SQL)
        res["execution_mode"] = REAL_EXECUTION_MODE
        return res

    def server_version(self) -> Dict[str, Any]:
        return self.query("SHOW SERVER VERSION")
