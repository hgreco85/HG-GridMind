"""Adversarial & Input Fragility Deep Test Suite for HG GridMind.

Evaluates 8 critical adversarial vectors:
1. Missing or Null Data (None fields, null lists, empty dictionaries)
2. Out-of-order Records (Reversed chronological order)
3. Inconsistent Timestamps (Malformed dates, None timestamps, non-string dates)
4. Contradictory Measurements (Simultaneous critical internal arc and neutral unbalance)
5. Mistyped Fields (Strings for numbers, integers for text, non-list flags)
6. Irrelevant Events (Noise logs, non-electrical events)
7. Duplicate IDs & Nonexistent Evidence (Duplicate row_ids, ghost citations)
8. Out-of-domain Inputs (Healthcare / e-commerce payloads)

Verifies zero unhandled exceptions, graceful degradation, and fail-closed safety.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.agent import GridMindCommander
from src.gate import HumanApprovalGate, HumanApprovalRequiredError


class MockConnector:
    def __init__(self, data):
        self._data = data

    def execute_federated_query(self, query_intent="INCIDENT_FEDERATION"):
        sources = self._data.get("synthetic_sources", {})
        tickets = sources.get("tickets_database", []) if isinstance(sources, dict) else []
        maintenance = sources.get("maintenance_history", []) if isinstance(sources, dict) else []
        scada = sources.get("scada_telemetry", []) if isinstance(sources, dict) else []
        if tickets is None:
            tickets = []
        if maintenance is None:
            maintenance = []
        if scada is None:
            scada = []
        return {
            "incident_id": self._data.get("incident_id", "ADV-TEST"),
            "asset_id": self._data.get("asset_id", "ADV-ASSET"),
            "initial_report": self._data.get("initial_operator_report", {}),
            "tickets": tickets,
            "maintenance": maintenance,
            "scada": scada,
            "synthetic_sources": sources,
            "metadata": {"test": True},
        }


class TestAdversarialDeepRobustness(unittest.TestCase):
    """Deep adversarial test cases ensuring no unhandled crashes across edge cases."""

    def test_01_missing_or_null_data(self):
        """Vector 1: Ensures None fields and null lists do not raise TypeError."""
        payload = {
            "incident_id": "ADV-01",
            "asset_id": "TR-NULL",
            "synthetic_sources": {
                "scada_telemetry": [{"row_id": "S1", "current_phase_a_amps": None, "relay_flags": None}],
                "maintenance_history": [{"row_id": "M1", "action": None, "result_status": None}],
                "tickets_database": None,
            },
        }
        conn = MockConnector(payload)
        commander = GridMindCommander(connector=conn)
        diagnosis = commander.investigate_incident()
        self.assertIsNotNone(diagnosis.initial_verdict)
        self.assertTrue(len(diagnosis.confirmed_root_cause) > 0)

    def test_02_out_of_order_records(self):
        """Vector 2: Ensures out-of-order records are sorted and evaluated accurately."""
        payload = {
            "incident_id": "ADV-02",
            "asset_id": "TR-ORDER",
            "synthetic_sources": {
                "scada_telemetry": [
                    {"row_id": "S2", "timestamp": "2026-10-22T10:00:00Z", "current_phase_a_amps": 200, "current_phase_b_amps": 450, "neutral_current_amps": 200, "relay_flags": []},
                    {"row_id": "S1", "timestamp": "2026-10-20T10:00:00Z", "current_phase_a_amps": 200, "current_phase_b_amps": 200, "neutral_current_amps": 0, "relay_flags": []},
                ],
                "maintenance_history": [
                    {"row_id": "M2", "action": "Termografia", "result_status": "WARNING", "timestamp": "2026-10-21T00:00:00Z"},
                    {"row_id": "M1", "action": "DGA cromatografia", "result_status": "NORMAL", "timestamp": "2026-10-19T00:00:00Z"},
                ],
            },
        }
        conn = MockConnector(payload)
        commander = GridMindCommander(connector=conn)
        diagnosis = commander.investigate_incident()
        self.assertEqual(diagnosis.initial_verdict, "REJECTED_AS_FALSE_CORRELATION")

    def test_03_inconsistent_timestamps(self):
        """Vector 3: Ensures None or malformed timestamp strings do not cause sorting failure."""
        payload = {
            "incident_id": "ADV-03",
            "asset_id": "TR-TIME",
            "synthetic_sources": {
                "scada_telemetry": [
                    {"row_id": "S1", "timestamp": None, "current_phase_a_amps": 100, "current_phase_b_amps": 100, "neutral_current_amps": 0, "relay_flags": []},
                    {"row_id": "S2", "timestamp": "INVALID_DATE_FORMAT_99999", "current_phase_a_amps": 100, "current_phase_b_amps": 100, "neutral_current_amps": 0, "relay_flags": []},
                ],
                "maintenance_history": [
                    {"row_id": "M1", "timestamp": "1970-01-01T00:00:00Z", "action": "DGA", "result_status": "NORMAL"},
                ],
            },
        }
        conn = MockConnector(payload)
        commander = GridMindCommander(connector=conn)
        diagnosis = commander.investigate_incident()
        self.assertIsNotNone(diagnosis.initial_verdict)

    def test_04_contradictory_measurements(self):
        """Vector 4: Ensures contradictory data resolves deterministically through priority hierarchy."""
        payload = {
            "incident_id": "ADV-04",
            "asset_id": "TR-CONTRADICTION",
            "synthetic_sources": {
                "scada_telemetry": [
                    {"row_id": "S1", "current_phase_a_amps": 2000, "current_phase_b_amps": 2000, "current_phase_c_amps": 2000, "neutral_current_amps": 500, "relay_flags": ["BUCHHOLZ_TRIP", "FEEDER_50P_TRIP"]},
                ],
                "maintenance_history": [
                    {"row_id": "M1", "action": "DGA cromatografia", "result_status": "CRITICAL_ALARM", "details": "Acetylene 50ppm"},
                    {"row_id": "M2", "action": "DGA cromatografia", "result_status": "NORMAL", "details": "Acetylene 0.1ppm"},
                    {"row_id": "M3", "action": "Termografia infrarroja", "result_status": "WARNING"},
                ],
            },
        }
        conn = MockConnector(payload)
        commander = GridMindCommander(connector=conn)
        diagnosis = commander.investigate_incident()
        self.assertEqual(diagnosis.initial_verdict, "CONFIRMED_INTERNAL_CATASTROPHIC_FAILURE")

    def test_05_mistyped_fields(self):
        """Vector 5: Ensures non-string actions or numeric strings do not cause crashes."""
        payload = {
            "incident_id": "ADV-05",
            "asset_id": "TR-TYPES",
            "synthetic_sources": {
                "scada_telemetry": [
                    {"row_id": "S1", "current_phase_a_amps": "210.4", "current_phase_b_amps": "445.8", "current_phase_c_amps": "195.2", "neutral_current_amps": "268.1", "relay_flags": "NOT_A_LIST"},
                ],
                "maintenance_history": [
                    {"row_id": "M1", "action": 12345, "result_status": ["NORMAL"]},
                ],
            },
        }
        conn = MockConnector(payload)
        commander = GridMindCommander(connector=conn)
        diagnosis = commander.investigate_incident()
        self.assertIsNotNone(diagnosis.initial_verdict)

    def test_06_irrelevant_events(self):
        """Vector 6: Ensures operational noise gracefully yields inconclusive verdict without hallucinations."""
        payload = {
            "incident_id": "ADV-06",
            "asset_id": "TR-NOISE",
            "synthetic_sources": {
                "scada_telemetry": [
                    {"row_id": "S_NOISE", "event": "Substation door opened", "temperature_ambient": 22.1, "current_phase_a_amps": 50, "current_phase_b_amps": 50, "current_phase_c_amps": 50, "neutral_current_amps": 0, "relay_flags": []},
                ],
                "maintenance_history": [
                    {"row_id": "M_NOISE", "action": "Lawn mowing around fence", "result_status": "COMPLETED"},
                ],
                "tickets_database": [
                    {"row_id": "T_NOISE", "description": "Streetlight bulb flickered on 4th street"},
                ],
            },
        }
        conn = MockConnector(payload)
        commander = GridMindCommander(connector=conn)
        diagnosis = commander.investigate_incident()
        self.assertEqual(diagnosis.initial_verdict, "INCONCLUSIVE_FURTHER_DIAGNOSTIC_REQUIRED")

    def test_07_duplicate_ids_and_citation_dedup(self):
        """Vector 7: Ensures duplicate row_ids do not create duplicate citations."""
        payload = {
            "incident_id": "ADV-07",
            "asset_id": "TR-DUPES",
            "synthetic_sources": {
                "scada_telemetry": [
                    {"row_id": "DUP-01", "current_phase_a_amps": 200, "current_phase_b_amps": 450, "neutral_current_amps": 250, "relay_flags": []},
                    {"row_id": "DUP-01", "current_phase_a_amps": 200, "current_phase_b_amps": 450, "neutral_current_amps": 250, "relay_flags": []},
                ],
                "maintenance_history": [
                    {"row_id": "DUP-01", "action": "Termografia", "result_status": "WARNING"},
                    {"row_id": "DUP-01", "action": "DGA cromatografia", "result_status": "NORMAL"},
                ],
            },
        }
        conn = MockConnector(payload)
        commander = GridMindCommander(connector=conn)
        diagnosis = commander.investigate_incident()
        # Verify citations are strictly deduplicated by (table, row_id)
        seen = set()
        for cit in diagnosis.evidence_trail:
            key = (cit.source_table, cit.row_id)
            self.assertNotIn(key, seen, f"Duplicate citation found: {key}")
            seen.add(key)

    def test_08_out_of_domain_input(self):
        """Vector 8: Ensures non-electrical domain input is categorized as inconclusive."""
        payload = {
            "incident_id": "ADV-08",
            "asset_id": "PATIENT-994",
            "domain": "HEALTHCARE",
            "synthetic_sources": {
                "scada_telemetry": [
                    {"row_id": "HR-01", "heart_rate": 72, "blood_pressure": "120/80"},
                ],
                "maintenance_history": [
                    {"row_id": "MED-01", "action": "Blood test", "cholesterol": 190},
                ],
            },
        }
        conn = MockConnector(payload)
        commander = GridMindCommander(connector=conn)
        diagnosis = commander.investigate_incident()
        self.assertEqual(diagnosis.initial_verdict, "INCONCLUSIVE_FURTHER_DIAGNOSTIC_REQUIRED")


if __name__ == "__main__":
    unittest.main()
