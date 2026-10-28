"""Zetaris Virtual Data Fabric Adapter for HG GridMind.

Two clearly separated execution paths, one API:

``REAL`` (preferred when available)
    Executes the contract's Lightning SQL on an **authentic** Zetaris engine
    (local docker compose, v2.4.3.1, official JDBC driver) through
    :mod:`src.sponsors.zetaris_real`. The engine returns the rows; nothing is
    replayed from the fixtures.

``SIMULATION`` (fallback, always labelled)
    The deterministic offline path used by judges without the stack: the query
    plan is reported and the *fixture* rows are returned. No engine is
    contacted. Every simulation result carries ``is_simulation: true``,
    ``simulated: true`` and a human-readable ``simulation_disclosure`` so it can
    never be mistaken for engine output.

Opt-in rules
------------
* ``use_real_engine=True`` (or ``GRIDMIND_ZETARIS_REAL=1``) requests the real path.
* The real path still needs ``ZETARIS_JDBC_JAR`` + ``ZETARIS_PASSWORD`` + ``java``.
* Any problem (not configured, engine down, engine error) downgrades to the
  simulation **without raising** and records the reason, so GridMind never breaks.

Federated sources (zero-ETL, in place)
--------------------------------------
* SCADA high-frequency telemetry        -> PostgreSQL JDBC datasource (``gridmind_scada_pg``)
* DGA chromatography / thermography     -> CSV Lightning filestore table
* Outage / work-order tickets           -> CSV Lightning filestore table
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:  # keep the adapter importable on its own (no hard dependency on the bridge)
    from src.sponsors.zetaris_real import (
        REAL_EXECUTION_MODE,
        ZetarisRealEngine,
        ZetarisRealEngineUnavailable,
    )
except ImportError:  # pragma: no cover - package layout variant
    from sponsors.zetaris_real import (  # type: ignore
        REAL_EXECUTION_MODE,
        ZetarisRealEngine,
        ZetarisRealEngineUnavailable,
    )

# Kept for backwards compatibility with existing consumers/tests; the value now
# means "deterministic simulation", never "a virtual engine answered".
SIMULATION_MODE = "LOCAL_VIRTUAL_FEDERATION"
SIMULATION_DISCLOSURE = (
    "SIMULATION: deterministic replay of the incident fixture rows. No Zetaris engine was "
    "contacted and the SQL below was not executed. Enable the real engine "
    "(GRIDMIND_ZETARIS_REAL=1 + ZETARIS_JDBC_JAR + ZETARIS_PASSWORD) for executed results."
)


@dataclass(frozen=True)
class ZetarisQueryContract:
    query_name: str
    target_tables: tuple[str, ...]
    lightning_sql: str
    cost_usd: float = 0.0


class ZetarisVirtualDataFabric:
    """Real-first Zetaris query harness with an explicit, labelled simulation fallback."""

    #: Contract catalogue. ``lightning_sql`` documents the dialect; the SQL that a
    #: real run actually executes lives in :mod:`src.sponsors.zetaris_real` and
    #: uses the registered real table names (``gridmind_scada_pg.*``,
    #: ``gridmind_files.*``), not the illustrative ``zetaris_virtual.*`` alias.
    LIGHTNING_SQL_TEMPLATES: Dict[str, ZetarisQueryContract] = {
        "INCIDENT_FEDERATION": ZetarisQueryContract(
            query_name="INCIDENT_FEDERATION",
            target_tables=("scada_telemetry", "maintenance_history", "tickets_database"),
            lightning_sql="""
                SELECT 
                    s.ts, s.current_phase_b_amps, s.neutral_current_amps,
                    m.row_id as maint_row_id, m.verdict, m.acetylene_ppm,
                    t.row_id as ticket_row_id, t.ticket_type, t.reported_at
                FROM gridmind_scada_pg.scada_telemetry s
                JOIN gridmind_files.maintenance_history m
                     ON m.asset_id = s.asset_id AND m.verdict <> 'NORMAL'
                JOIN gridmind_files.tickets_database t
                     ON t.affected_feeder = s.feeder_id
                WHERE s.asset_id = :asset_id AND s.neutral_current_amps > :neutral_threshold
                ORDER BY s.ts DESC, t.row_id
            """.strip(),
        ),
        "DGA_GAS_AUDIT": ZetarisQueryContract(
            query_name="DGA_GAS_AUDIT",
            target_tables=("maintenance_history",),
            lightning_sql="""
                SELECT row_id, sample_date, hydrogen_ppm, acetylene_ppm, methane_ppm, verdict
                FROM gridmind_files.maintenance_history
                WHERE asset_id = :asset_id AND test_type = 'DGA_CHROMATOGRAPHY'
                ORDER BY sample_date DESC LIMIT 5
            """.strip(),
        ),
        "SCADA_CURRENT_UNBALANCE": ZetarisQueryContract(
            query_name="SCADA_CURRENT_UNBALANCE",
            target_tables=("scada_telemetry",),
            lightning_sql="""
                SELECT row_id, ts, current_phase_a_amps, current_phase_b_amps,
                       current_phase_c_amps, neutral_current_amps
                FROM gridmind_scada_pg.scada_telemetry
                WHERE asset_id = :asset_id
                ORDER BY ts DESC LIMIT 10
            """.strip(),
        ),
    }

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        api_key: Optional[str] = None,
        real_engine: Optional["ZetarisRealEngine"] = None,
        use_real_engine: Optional[bool] = None,
    ):
        self.endpoint_url = endpoint_url or "zetaris://local.virtual.engine:10000"
        self.api_key = api_key or "FREE_TIER_OR_LOCAL_VIRTUAL"
        # Opt-in: explicit argument wins, else GRIDMIND_ZETARIS_REAL=1. Default: simulation.
        if use_real_engine is None:
            use_real_engine = os.environ.get("GRIDMIND_ZETARIS_REAL") == "1"
        self.use_real_engine = use_real_engine
        self.real_engine = real_engine or ZetarisRealEngine()

    # -- capability --------------------------------------------------------
    def real_engine_status(self) -> Dict[str, Any]:
        """Describes the real path without contacting it."""
        check = getattr(self.real_engine, "configuration_problem", None)
        problem = check() if callable(check) else None
        return {
            "requested": self.use_real_engine,
            "configured": problem is None,
            "available": self.use_real_engine and problem is None,
            "reason": problem if problem else "real engine configured",
            "execution_mode": REAL_EXECUTION_MODE if (self.use_real_engine and problem is None) else SIMULATION_MODE,
        }

    def explain_query_plan(self, query_intent: str) -> Dict[str, Any]:
        """Describes the SIMULATION plan for one contract, plus the real-engine status.

        ``execute_virtual_query`` always replays fixture rows, so its plan is always
        labelled as a simulation even when a real engine is configured. Executed rows and
        their mode come from :meth:`execute_query_contract`.
        """
        contract = self.LIGHTNING_SQL_TEMPLATES.get(query_intent)
        if not contract:
            raise ValueError(f"Unknown Zetaris query contract: {query_intent}")
        status = self.real_engine_status()
        return {
            "query_name": contract.query_name,
            "engine": "SIMULATED (no engine contacted)",
            "target_dialect": "Zetaris Lightning SQL",
            "execution_mode": SIMULATION_MODE,
            "is_simulation": True,
            "simulated": True,
            "simulation_disclosure": SIMULATION_DISCLOSURE,
            "zero_etl_guaranteed": False,
            "sql": contract.lightning_sql,
            "target_tables": list(contract.target_tables),
            "data_movement_required": False,
            "incremental_cost_usd": 0.0,
            "real_engine": status,
        }

    # -- real path ---------------------------------------------------------
    def execute_query_contract(
        self,
        query_intent: str = "INCIDENT_FEDERATION",
        asset_id: Optional[str] = None,
        neutral_threshold: float = 15.0,
    ) -> Dict[str, Any]:
        """Real-first execution of one contract. Never raises.

        Returns ``{"used": True, ...engine rows...}`` when a real engine answered, or
        ``{"used": False, "fallback": "SIMULATION", "is_simulation": True, ...}`` with the
        reason when it did not. Callers must keep the simulation flag when they fall back.
        """
        if self.LIGHTNING_SQL_TEMPLATES.get(query_intent) is None:
            raise ValueError(f"Unknown Zetaris query contract: {query_intent}")
        status = self.real_engine_status()
        if not self.use_real_engine:
            return {
                "used": False,
                "fallback": "SIMULATION",
                "is_simulation": True,
                "execution_mode": SIMULATION_MODE,
                "reason": "real engine not requested (set GRIDMIND_ZETARIS_REAL=1)",
            }
        if not status["configured"]:
            return {
                "used": False,
                "fallback": "SIMULATION",
                "is_simulation": True,
                "execution_mode": SIMULATION_MODE,
                "reason": status["reason"],
            }
        try:
            if query_intent == "INCIDENT_FEDERATION":
                if asset_id is None:
                    raise ValueError("asset_id is required for INCIDENT_FEDERATION")
                res = self.real_engine.incident_federation(str(asset_id), neutral_threshold)
            elif query_intent == "DGA_GAS_AUDIT":
                raise ValueError("DGA_GAS_AUDIT has no real-engine SQL yet")
            else:
                raise ValueError(f"{query_intent} has no real-engine SQL yet")
        except (ZetarisRealEngineUnavailable, ValueError) as exc:
            return {
                "used": False,
                "fallback": "SIMULATION",
                "is_simulation": True,
                "execution_mode": SIMULATION_MODE,
                "reason": str(exc)[:240],
            }
        return {
            "used": True,
            "is_simulation": False,
            "asset_id": asset_id,
            "execution_mode": REAL_EXECUTION_MODE,
            "engine_status": status,
            **res,
        }

    # -- simulation path ---------------------------------------------------
    def execute_virtual_query(self, query_intent: str, dataset_bundle: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministic SIMULATION: reports the plan and replays the fixture rows.

        This never contacts an engine. If you need executed rows call
        :meth:`execute_query_contract`.
        """
        plan = self.explain_query_plan(query_intent)
        sources = dataset_bundle.get("synthetic_sources", {})

        scada = sources.get("scada_telemetry", [])
        maint = sources.get("maintenance_history", [])
        tickets = sources.get("tickets_database", [])

        return {
            "execution_plan": plan,
            "results": {
                "scada_rows": scada,
                "maintenance_rows": maint,
                "ticket_rows": tickets,
            },
            "total_rows_evaluated": len(scada) + len(maint) + len(tickets),
            "exact_row_citations_available": True,
            "is_simulation": True,
            "simulated": True,
            "simulation_disclosure": SIMULATION_DISCLOSURE,
        }
