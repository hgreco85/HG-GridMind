"""Federated Data Connector for HG GridMind.

Utilizes Zetaris Virtual Data Fabric principles to join fragmented operational
data (SCADA, Maintenance DGA/Thermography, Tickets) without ETL data movement.
Completely standalone, deterministic, and offline-compatible.
"""

from __future__ import annotations

import json
from pathlib import Path
import os
from typing import Any, Dict, Optional
from src.sponsors.zetaris_adapter import ZetarisVirtualDataFabric
from src.sponsors.zetaris_real import ZetarisRealEngine, ZetarisRealEngineUnavailable


class FederatedDataConnector:
    """Connects to and executes federated queries across distributed utility data sources."""

    def __init__(
        self,
        fixture_path: Path,
        zetaris_endpoint: Optional[str] = None,
        use_real_engine: Optional[bool] = None,
        real_engine: Optional[ZetarisRealEngine] = None,
    ):
        self.fixture_path = fixture_path
        # Opt-in: explicit argument wins, else GRIDMIND_ZETARIS_REAL=1. Default is the offline mock.
        if use_real_engine is None:
            use_real_engine = os.environ.get("GRIDMIND_ZETARIS_REAL") == "1"
        self.use_real_engine = use_real_engine
        self.real_engine = real_engine or ZetarisRealEngine()
        self._data: Dict[str, Any] = {}
        self.zetaris_fabric = ZetarisVirtualDataFabric(endpoint_url=zetaris_endpoint)
        self.load()

    def load(self) -> None:
        """Loads data records from the local storage harness."""
        if not self.fixture_path.exists():
            raise FileNotFoundError(f"Incident fixture dataset not found: {self.fixture_path}")
        raw = self.fixture_path.read_text(encoding="utf-8")
        self._data = json.loads(raw)

    def execute_federated_query(self, query_intent: str = "INCIDENT_FEDERATION") -> Dict[str, Any]:
        """Executes a Zero-ETL federated query joining in-place records."""
        federated_execution = self.zetaris_fabric.execute_virtual_query(
            "INCIDENT_FEDERATION", self._data
        )

        sources = self._data.get("synthetic_sources", {})
        zetaris_real = self._try_real_engine()
        result = {
            "incident_id": self._data.get("incident_id", "UNKNOWN"),
            "asset_id": self._data.get("asset_id", "UNKNOWN"),
            "initial_report": self._data.get("initial_operator_report", {}),
            "tickets": sources.get("tickets_database", []),
            "maintenance": sources.get("maintenance_history", []),
            "scada": sources.get("scada_telemetry", []),
            "zetaris_execution": federated_execution["execution_plan"],
            "metadata": {
                "federation_engine": "Zetaris Virtual Data Fabric (Lightning SQL)",
                "sources_joined": 3,
                "rows_evaluated": federated_execution["total_rows_evaluated"],
                "cost_usd": 0.0,
                "zero_etl": True,
            },
        }
        result["zetaris_real"] = zetaris_real
        return result

    def _try_real_engine(self) -> Dict[str, Any]:
        """Optionally runs the same federation on the real Zetaris engine.

        Never raises: on any problem returns ``{"used": False, "fallback": "MOCK", ...}`` so the
        deterministic offline pipeline is unaffected. Real rows are additive evidence; they are
        keyed by the real engine's own synthetic dataset (see integrations/zetaris/).
        """
        if not self.use_real_engine:
            return {"used": False, "fallback": "MOCK", "reason": "real engine not requested"}
        asset_id = os.environ.get("GRIDMIND_ZETARIS_ASSET_ID") or self._data.get("asset_id", "")
        try:
            res = self.real_engine.incident_federation(str(asset_id))
        except (ZetarisRealEngineUnavailable, ValueError) as exc:
            return {"used": False, "fallback": "MOCK", "reason": str(exc)[:240]}
        return {"used": True, "asset_id": asset_id, **res}

