"""Meterless Context Engine Conformance Test Suite.

Verifies conformance to Meterless Open Core (Apache 2.0) specifications:
1. H-MEM (Hierarchical Memory): Canonical memory schema, tiered storage (short_term,
   working, long_term), null-safe chronological normalization, and provenance tracking.
2. Markovian State Engine: ChunkConfig bounds, structured carryover state blocks,
   marker protocol ([STATE_CHECKPOINT], [TASK_COMPLETE]), and dynamic state transition probabilities.
3. World Model Engine: Entity-Context-Relationship model with stable IDs, physical electrical
   invariants (Kirchhoff, Joule, IEEE C57.104 gas limits), and dynamic falsification evaluation.
"""

from __future__ import annotations

import unittest
from src.sponsors.meterless_adapter import (
    ChunkConfig,
    HMEMRecord,
    MeterlessContextLayer,
    OperationalState,
)


class TestMeterlessConformance(unittest.TestCase):
    """Conformance tests for Meterless open core specification implementation."""

    def test_hmem_canonical_memory_model_and_provenance(self):
        """H-MEM: Verifies memory records contain mandatory provenance, layer, and source."""
        meterless = MeterlessContextLayer(incident_id="INC-CONF-001", asset_id="TR-800")
        events = [
            {"row_id": "MAINT-1", "action": "DGA analysis", "details": "Normal", "date": "2026-10-18"},
            {"row_id": "SCADA-1", "current_phase_a_amps": 150.0, "timestamp": "2026-10-20T12:00:00Z"},
        ]
        meterless.ingest_h_mem_timeline(events)

        self.assertEqual(len(meterless.memory_records), 2)
        maint_rec = meterless.memory_records[0]
        scada_rec = meterless.memory_records[1]

        # Verify tiered storage classification
        self.assertEqual(maint_rec.layer, "long_term")
        self.assertEqual(scada_rec.layer, "working")

        # Verify mandatory provenance and reliability fields
        self.assertIn("incident_id", maint_rec.provenance)
        self.assertGreater(maint_rec.confidence, 0.0)
        self.assertTrue(maint_rec.source.startswith("zetaris_virtual."))
        self.assertIn("INC-CONF-001", maint_rec.tags)

    def test_hmem_null_and_malformed_timestamp_tolerance(self):
        """H-MEM: Verifies graceful handling of None, missing, or malformed timestamps without crashing."""
        meterless = MeterlessContextLayer(incident_id="INC-CONF-002")
        messy_events = [
            {"row_id": "EVT-1", "details": "No timestamp key"},
            {"row_id": "EVT-2", "timestamp": None, "details": "Explicit None timestamp"},
            {"row_id": "EVT-3", "timestamp": "2026-10-21T09:00:00Z", "details": "Valid ISO timestamp"},
            {"row_id": "EVT-4", "date": 123456, "details": "Integer timestamp"},
            None,  # Non-dict event
        ]
        # Must not raise TypeError
        sorted_events = meterless.ingest_h_mem_timeline(messy_events)
        self.assertEqual(len(sorted_events), 4)
        self.assertEqual(len(meterless.timeline_events), 4)

    def test_markovian_chunk_config_and_marker_protocol(self):
        """Markovian: Verifies ChunkConfig parameters and structured carryover marker protocol."""
        meterless = MeterlessContextLayer(incident_id="INC-CONF-003", asset_id="TR-900")
        events = [
            {"row_id": "M1", "result_status": "NORMAL", "action": "DGA", "date": "2026-10-18T10:00:00Z"},
            {"row_id": "M2", "result_status": "WARNING", "action": "IR Termografia hot spot", "date": "2026-10-19T10:00:00Z"},
            {"row_id": "S1", "current_phase_a_amps": 200, "current_phase_b_amps": 500, "neutral_current_amps": 250, "timestamp": "2026-10-20T10:00:00Z"},
            {"row_id": "S2", "relay_flags": ["FEEDER_TRIP_50N"], "timestamp": "2026-10-20T10:05:00Z"},
        ]
        meterless.ingest_h_mem_timeline(events)
        transitions = meterless.compute_markovian_transitions()

        # Dynamic state progression
        self.assertGreaterEqual(len(transitions), 4)
        self.assertEqual(transitions[0].state_name, "NORMAL_STEADY_STATE")
        self.assertEqual(transitions[-1].state_name, "PROTECTION_TRIP")

        # Context bundle marker protocol check
        bundle = meterless.export_context_bundle()
        marker_protocol = bundle["marker_protocol"]
        self.assertEqual(marker_protocol["checkpoint"], "[STATE_CHECKPOINT]")
        self.assertEqual(marker_protocol["complete"], "[TASK_COMPLETE]")

        carryover = marker_protocol["carryover_state"]
        self.assertIn("COMPLETED:", carryover)
        self.assertIn("REMAINING:", carryover)
        self.assertIn("DECISIONS:", carryover)
        self.assertIn("CONTEXT:", carryover)

        # ChunkConfig compliance
        cfg = bundle["chunk_config"]
        self.assertEqual(cfg["chunk_size"], 8000)
        self.assertEqual(cfg["carryover_tokens"], 800)
        self.assertEqual(cfg["max_chunks"], 24)

    def test_world_model_dynamic_falsification_checks(self):
        """World Model: Verifies dynamic evaluation of physical assertions based on actual sensor evidence."""
        # Case A: Real internal arc (Acetylene > 2.0 ppm)
        meterless_arc = MeterlessContextLayer(incident_id="INC-ARC", asset_id="TR-ARC-1")
        meterless_arc.ingest_h_mem_timeline([
            {"details": "DGA Acetileno: 14.5 ppm, Hidrógeno: 400 ppm", "result_status": "CRITICAL_ALARM"},
        ])
        graph_arc = meterless_arc.build_world_model_graph()
        self.assertTrue(graph_arc["falsification_checks"]["internal_arc_possible"])
        self.assertEqual(graph_arc["transformer"]["id"], "TR-ARC-1")

        # Case B: Terminal overheating (Delta T = 45C, neutral current 280A)
        meterless_therm = MeterlessContextLayer(incident_id="INC-THERM", asset_id="TR-THERM-2")
        meterless_therm.ingest_h_mem_timeline([
            {"details": "IR Termografía delta T = 45 C sobre ambiente", "neutral_current_amps": 280.0},
        ])
        graph_therm = meterless_therm.build_world_model_graph()
        self.assertFalse(graph_therm["falsification_checks"]["internal_arc_possible"])
        self.assertTrue(graph_therm["falsification_checks"]["terminal_overheating_confirmed"])
        self.assertEqual(graph_therm["transformer"]["id"], "TR-THERM-2")


if __name__ == "__main__":
    unittest.main()
