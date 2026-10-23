"""Comprehensive Offline Unit Test Suite for HG GridMind.

Challenge 02: The Agent That Can Explain Why.
100% offline, deterministic, zero network calls, zero paid API spend ($0.00).
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from src.agent import GridMindCommander, IncidentDiagnosis
from src.data_connector import FederatedDataConnector
from src.gate import HumanApprovalGate, HumanApprovalRequiredError
from src.sponsors.cursor_audit import CursorEnvironmentAudit
from src.sponsors.meterless_adapter import MeterlessContextLayer
from src.sponsors.nemotron_adapter import NemotronCausalReasoner
from src.sponsors.zetaris_adapter import ZetarisVirtualDataFabric


class TestGridMindComprehensiveSuite(unittest.TestCase):
    def setUp(self):
        self.fixture_path = (
            Path(__file__).resolve().parent.parent / "fixtures" / "incident_INC_2026_UTIL_8812.json"
        )
        self.connector = FederatedDataConnector(self.fixture_path)

    def test_zetaris_virtual_data_fabric_query_plan(self):
        fabric = ZetarisVirtualDataFabric()
        plan = fabric.explain_query_plan("INCIDENT_FEDERATION")
        self.assertEqual(plan["engine"], "Zetaris Lightning SQL Engine")
        self.assertTrue(plan["zero_etl_guaranteed"])
        self.assertIn("scada_telemetry", plan["target_tables"])
        self.assertIn("maintenance_history", plan["target_tables"])
        self.assertIn("tickets_database", plan["target_tables"])

    def test_meterless_context_engines(self):
        meterless = MeterlessContextLayer("INC-2026-UTIL-8812")
        transitions = meterless.compute_markovian_transitions()
        self.assertGreaterEqual(len(transitions), 4)
        self.assertEqual(transitions[0].state_name, "NORMAL_STEADY_STATE")
        self.assertEqual(transitions[-1].state_name, "PROTECTION_TRIP")

        world_model = meterless.build_world_model_graph()
        self.assertIn("substation", world_model)
        self.assertFalse(world_model["falsification_checks"]["internal_arc_possible"])
        self.assertTrue(world_model["falsification_checks"]["terminal_overheating_confirmed"])

    def test_nemotron_causal_reasoner_falsification(self):
        reasoner = NemotronCausalReasoner()
        hypotheses = reasoner.formulate_competing_hypotheses()
        self.assertEqual(len(hypotheses), 3)

        h1 = next(h for h in hypotheses if h.hypothesis_id == "H1")
        h2 = next(h for h in hypotheses if h.hypothesis_id == "H2")
        h3 = next(h for h in hypotheses if h.hypothesis_id == "H3")

        self.assertEqual(h1.status, "FALSIFIED")
        self.assertEqual(h2.status, "FALSIFIED")
        self.assertEqual(h3.status, "CONFIRMED")
        self.assertIn("MAINT-ROW-99182", h1.falsification_evidence)

    def test_causal_investigation_and_evidence_citations(self):
        commander = GridMindCommander(self.connector)
        diag = commander.investigate_incident()

        self.assertEqual(diag.incident_id, "INC-2026-UTIL-8812")
        self.assertEqual(diag.asset_id, "TR-404")
        self.assertEqual(diag.initial_verdict, "REJECTED_AS_FALSE_CORRELATION")

        # Verify exact row-level citations exist
        row_ids = [c.row_id for c in diag.evidence_trail]
        self.assertIn("MAINT-ROW-99182", row_ids)
        self.assertIn("MAINT-ROW-99204", row_ids)
        self.assertIn("SCADA-ROW-55102", row_ids)

        # Verify active falsification list
        falsified_titles = [f["hypothesis"] for f in diag.falsified_hypotheses]
        self.assertTrue(any("H1:" in t for t in falsified_titles))
        self.assertTrue(any("H2:" in t for t in falsified_titles))

        # Verify audit hash
        self.assertTrue(diag.audit_ack_hash.startswith("HG-GRIDMIND-ACK-"))

    def test_human_approval_gate_fail_closed_without_token(self):
        gate = HumanApprovalGate()
        commander = GridMindCommander(self.connector, gate)
        diag = commander.investigate_incident()

        self.assertFalse(diag.is_authorized_by_human)
        self.assertTrue(diag.approval_required)

        with self.assertRaises(HumanApprovalRequiredError) as ctx:
            commander.dispatch_remediation_task(diag)

        self.assertIn("Action blocked", str(ctx.exception))

    def test_human_approval_gate_passes_with_authenticated_token(self):
        gate = HumanApprovalGate.issue_token(
            operator_name="Hernan Greco",
            operator_role="Lead Power Grid Dispatcher",
            action_summary="Feeder load transfer and terminal torque inspection",
        )
        commander = GridMindCommander(self.connector, gate)
        diag = commander.investigate_incident()

        self.assertTrue(diag.is_authorized_by_human)
        receipt = commander.dispatch_remediation_task(diag)

        self.assertEqual(receipt["status"], "DISPATCHED_TO_GRID_OPERATIONS")
        self.assertEqual(receipt["authorized_by"], "Hernan Greco")
        self.assertTrue(receipt["approval_token"].startswith("HUMAN-SIGNOFF-"))
        self.assertEqual(receipt["spend_usd"], 0.0)

    def test_cursor_environment_audit(self):
        audit = CursorEnvironmentAudit()
        res = audit.to_dict()
        self.assertEqual(res["editor"], "Cursor IDE")
        self.assertEqual(res["sponsor_tech_compliance"], "PASS")
        self.assertEqual(res["incremental_spend_usd"], 0.0)


if __name__ == "__main__":
    unittest.main()
