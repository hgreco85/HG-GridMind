"""Comprehensive Offline Unit Test Suite for HG GridMind.

Challenge 02: The Agent That Can Explain Why.
100% offline, deterministic, zero network calls, zero paid API spend ($0.00).
Includes multi-scenario generalization and adversarial robustness.
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
        self.fixtures_dir = Path(__file__).resolve().parent.parent / "fixtures"
        self.fixture_8812 = self.fixtures_dir / "incident_INC_2026_UTIL_8812.json"
        self.fixture_9041 = self.fixtures_dir / "incident_INC_2026_UTIL_9041.json"
        self.fixture_7720 = self.fixtures_dir / "incident_INC_2026_UTIL_7720.json"
        self.fixture_5501 = self.fixtures_dir / "incident_INC_2026_UTIL_5501.json"
        self.connector = FederatedDataConnector(self.fixture_8812)

    def test_zetaris_virtual_data_fabric_query_plan(self):
        fabric = ZetarisVirtualDataFabric()
        plan = fabric.explain_query_plan("INCIDENT_FEDERATION")
        # Default plan is the simulation: labelled as such, never claiming engine output.
        self.assertEqual(plan["engine"], "SIMULATED (no engine contacted)")
        self.assertTrue(plan["is_simulation"])
        self.assertFalse(plan["zero_etl_guaranteed"])
        self.assertIn("SIMULATION", plan["simulation_disclosure"])
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

    def test_nemotron_causal_reasoner_evaluation(self):
        reasoner = NemotronCausalReasoner()
        bundle = self.connector.execute_federated_query("INCIDENT_FEDERATION")
        meterless = MeterlessContextLayer("INC-2026-UTIL-8812")
        context = meterless.export_context_bundle()

        res = reasoner.generate_causal_explanation(bundle, context)
        self.assertEqual(res["verdict_code"], "REJECTED_AS_FALSE_CORRELATION")
        self.assertEqual(res["execution_mode"], "DETERMINISTIC_PHYSICAL_REASONER")
        self.assertIn("MAINT-ROW-99182", res["narrative_explanation"])

    def test_adversarial_scenario_real_internal_failure(self):
        """Tests that incident 9041 correctly triggers internal arc diagnosis."""
        connector = FederatedDataConnector(self.fixture_9041)
        commander = GridMindCommander(connector)
        diag = commander.investigate_incident()

        self.assertEqual(diag.initial_verdict, "CONFIRMED_INTERNAL_CATASTROPHIC_FAILURE")
        self.assertIn("Arco eléctrico interno", diag.confirmed_root_cause)
        self.assertIn("MAINT-ROW-88401", [c.row_id for c in diag.evidence_trail])

    def test_adversarial_scenario_downstream_line_fault(self):
        """Tests that incident 7720 correctly identifies external line fault."""
        connector = FederatedDataConnector(self.fixture_7720)
        commander = GridMindCommander(connector)
        diag = commander.investigate_incident()

        self.assertEqual(diag.initial_verdict, "CONFIRMED_DOWNSTREAM_FEEDER_FAULT")
        self.assertIn("Cortocircuito trifásico simétrico", diag.confirmed_root_cause)

    def test_adversarial_scenario_missing_evidence_abstention(self):
        """Tests that incident 5501 strictly abstains to prevent hallucinations."""
        connector = FederatedDataConnector(self.fixture_5501)
        commander = GridMindCommander(connector)
        diag = commander.investigate_incident()

        self.assertEqual(diag.initial_verdict, "ABSTENTION_INSUFFICIENT_EVIDENCE")
        self.assertIn("Abstención obligatoria", diag.confirmed_root_cause)

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
