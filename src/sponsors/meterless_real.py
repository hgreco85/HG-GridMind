"""Opt-in bridge from HG GridMind to the REAL Meterless H-MEM engine.

``meterless_adapter.py`` (pre-existing) is a local, deterministic *re-implementation* of the
Meterless ideas in Python. THIS module instead runs the actual Meterless H-MEM reference engine
(Apache-2.0, https://github.com/Meterless/Meterless, ``engines/hmem/reference``) as a Node/TypeScript
subprocess: GridMind pushes evidence facts (e.g. real Zetaris federated rows) into H-MEM, asks it
questions, and gets back the engine's own ranked memories, retrieval trace and TrustLedger history.

Free by construction: Meterless engines need no API key, account or credits.

Setup once:  bash integrations/meterless/setup.sh     (needs node >= 18, npm, git)
Opt-in:      GRIDMIND_METERLESS_REAL=1  or  FederatedDataConnector(use_real_meterless=True)
Any problem raises ``MeterlessRealEngineUnavailable``; callers fall back to the mimic and label it.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
MET_DIR = REPO_ROOT / "integrations" / "meterless"
REAL_EXECUTION_MODE = "REAL_METERLESS_HMEM_ENGINE"
_FEEDBACK = {"helpful", "not_helpful", "wrong"}


class MeterlessRealEngineUnavailable(RuntimeError):
    """Raised when the real Meterless H-MEM engine cannot be used."""


def facts_from_zetaris_rows(rows: List[Dict[str, Any]], asset_id: str) -> List[Dict[str, Any]]:
    """Turns federated Zetaris rows into one H-MEM fact per distinct source row (provenance kept)."""
    facts: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        sid = r.get("scada_row_id")
        if sid and sid not in facts:
            facts[sid] = {
                "source": f"zetaris:gridmind_scada_pg.scada_telemetry/{sid}",
                "content": (f"{sid} asset {asset_id} at {r.get('ts')}: phase-B current "
                            f"{float(r['current_phase_b_amps']):.1f} A, neutral current "
                            f"{float(r['neutral_current_amps']):.1f} A (neutral overload)"),
                "tags": [f"asset:{asset_id}", "kind:scada", "signal:neutral_current"],
            }
        mid = r.get("maint_row_id")
        if mid and mid not in facts:
            facts[mid] = {
                "source": f"zetaris:gridmind_files.maintenance_history/{mid}",
                "content": (f"{mid} asset {asset_id} DGA maintenance verdict {r.get('dga_verdict')}, "
                            f"acetylene {r.get('acetylene_ppm')} ppm (thermal hot spot, not arcing)"),
                "tags": [f"asset:{asset_id}", "kind:maintenance", "signal:dga"],
            }
        tid = r.get("ticket_row_id")
        if tid and tid not in facts:
            facts[tid] = {
                "source": f"zetaris:gridmind_files.tickets_database/{tid}",
                "content": (f"{tid} ticket {r.get('ticket_type')} reported at {r.get('reported_at')} "
                            f"on the feeder of asset {asset_id}"),
                "tags": [f"asset:{asset_id}", "kind:ticket"],
            }
    return list(facts.values())


class MeterlessHMemEngine:
    """Thin subprocess client for ``integrations/meterless/gridmind_hmem.ts``."""

    def __init__(self, state_dir: Optional[str] = None, timeout_s: int = 60):
        self.state_dir = state_dir or os.environ.get("METERLESS_STATE_DIR")
        self.timeout_s = timeout_s

    def configuration_problem(self) -> Optional[str]:
        if not shutil.which("node"):
            return "node not found on PATH"
        if not (MET_DIR / "vendor" / "hmem" / "src" / "index.ts").exists():
            return "H-MEM engine not vendored; run: bash integrations/meterless/setup.sh"
        if not (MET_DIR / "node_modules" / "tsx").exists():
            return "tsx missing; run: bash integrations/meterless/setup.sh"
        return None

    def available(self) -> bool:
        return self.configuration_problem() is None

    def ingest_and_recall(
        self,
        facts: List[Dict[str, Any]],
        questions: List[str],
        feedback: Optional[str] = None,
        top_n: int = 5,
    ) -> Dict[str, Any]:
        problem = self.configuration_problem()
        if problem:
            raise MeterlessRealEngineUnavailable(problem)
        if feedback is not None and feedback not in _FEEDBACK:
            raise ValueError(f"feedback must be one of {sorted(_FEEDBACK)}")
        payload = {"facts": facts, "questions": questions, "feedback": feedback, "topN": top_n}
        env = os.environ.copy()
        if self.state_dir:
            env["METERLESS_STATE_DIR"] = self.state_dir
        try:
            proc = subprocess.run(
                ["node", "--import", "tsx", "gridmind_hmem.ts"],
                cwd=str(MET_DIR), input=json.dumps(payload).encode("utf-8"),
                capture_output=True, timeout=self.timeout_s, env=env,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise MeterlessRealEngineUnavailable(f"H-MEM runner failed: {type(exc).__name__}") from exc
        out = proc.stdout.decode("utf-8", "replace").strip()
        if proc.returncode != 0 or not out.startswith("{"):
            tail = proc.stderr.decode("utf-8", "replace").strip().splitlines()[-1:]
            raise MeterlessRealEngineUnavailable(f"H-MEM error (exit {proc.returncode}): {tail[0][:200] if tail else 'no output'}")
        try:
            res = json.loads(out)
        except ValueError as exc:
            raise MeterlessRealEngineUnavailable("unparseable H-MEM output") from exc
        res["execution_mode"] = REAL_EXECUTION_MODE
        return res


def default_questions(asset_id: str) -> List[str]:
    return [
        f"why is the neutral current overloaded on {asset_id}",
        f"what does the dissolved gas analysis say about {asset_id}",
        f"which customer tickets relate to {asset_id}",
    ]
