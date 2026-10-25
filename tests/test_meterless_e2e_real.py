"""E2E Verification & Deliberate Disconnection Tests for Official Meterless Engine.

Verifies:
1. True end-to-end execution of official Meterless TypeScript engines:
   - H-MEM: Hierarchical memory ingestion and retrieval
   - World Model: Topological entity relationships and canonical state shape
   - Markovian: Multi-chunk operational state transitions and token efficiency
2. Deliberate disconnection test: Confirms that if the official Meterless engine bridge
   fails or is severed, GridMind strictly raises MeterlessBridgeDisconnectedError.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from src.agent import GridMindCommander
from src.data_connector import FederatedDataConnector
from src.sponsors.meterless_adapter import (
    MeterlessBridgeDisconnectedError,
    MeterlessContextLayer,
)

ROOT_DIR = Path(__file__).resolve().parent.parent


class TestMeterlessE2EReal(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture_9933 = ROOT_DIR / "fixtures" / "incident_INC_2026_UTIL_9933.json"
        self.assertTrue(self.fixture_9933.exists(), "Synthetic fixture 9933 must exist")
        self.connector = FederatedDataConnector(self.fixture_9933)

    def test_01_meterless_e2e_live_official_bridge(self) -> None:
        """Priority 2: End-to-end execution with official H-MEM, World Model, and Markovian engines."""
        commander = GridMindCommander(
            connector=self.connector,
            require_meterless_bridge=True,
        )
        diagnosis = commander.investigate_incident()

        # Check diagnosis completed successfully
        self.assertEqual(diagnosis.incident_id, "INC-2026-UTIL-9933")
        self.assertEqual(diagnosis.asset_id, "TR-505")

        # Verify sponsor_metadata contains official_bridge output
        meterless_meta = diagnosis.sponsor_metadata.get("meterless", {})
        self.assertIn("official_bridge", meterless_meta, "Official Meterless bridge must be present in metadata")
        bridge = meterless_meta["official_bridge"]

        # 1. H-MEM Verification
        self.assertEqual(bridge["meterless_bridge_version"], "1.0.0-official-conforming")
        self.assertEqual(bridge["hmem"]["records_ingested"], 4, "Must ingest 4 records (2 maintenance, 1 scada, 1 ticket)")
        self.assertGreaterEqual(bridge["hmem"]["retrieved_memories"], 1)

        # 2. World Model Verification
        self.assertTrue(bridge["world_model"]["substation_id"].startswith("ent_"))
        self.assertTrue(bridge["world_model"]["transformer_id"].startswith("ent_"))
        self.assertGreaterEqual(bridge["world_model"]["audit_events_count"], 3)
        self.assertTrue(len(bridge["world_model"]["canonical_shape_hash"]) > 0)

        # 3. Markovian Verification
        self.assertEqual(bridge["markovian"]["status"], "completed")
        self.assertGreaterEqual(bridge["markovian"]["chunks_evaluated"], 3)
        self.assertGreaterEqual(bridge["markovian"]["tokens_used"], 50)

    def test_02_meterless_e2e_deliberate_disconnection_failure(self) -> None:
        """Priority 2: Deliberate failure test - raises MeterlessBridgeDisconnectedError if severed."""
        layer = MeterlessContextLayer(incident_id="INC-TEST-FAIL", asset_id="TR-DISCONNECTED")
        dummy_bundle = {"initial_report": {"observed_symptom": "Test"}}

        # Sever the connection by providing an invalid script path
        with self.assertRaises(MeterlessBridgeDisconnectedError) as ctx:
            layer.execute_official_engine_bridge(
                bundle_data=dummy_bundle,
                require_official_bridge=True,
                bridge_script_path="non_existent_meterless_bridge.ts",
            )
        self.assertIn("Official Meterless engine bridge not found", str(ctx.exception))

        # Sever the connection via subprocess failure
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "Fatal: Meterless engine kernel panic"
            with self.assertRaises(MeterlessBridgeDisconnectedError) as ctx2:
                layer.execute_official_engine_bridge(
                    bundle_data=dummy_bundle,
                    require_official_bridge=True,
                )
            self.assertIn("Meterless engine kernel panic", str(ctx2.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
