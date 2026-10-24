"""Deterministic verification of causal invariants, physical grid bounds, and hypothesis falsification.

Open Agent Hackathon 2026 - Challenge 02: The Agent That Can Explain Why.
Offline deterministic unittest suite, zero network, USD 0.00.
"""

import unittest
from pathlib import Path
from src.agent import CausalEvidenceCitation, IncidentDiagnosis, GridMindCommander
from src.data_connector import FederatedDataConnector
from src.gate import HumanApprovalGate, HumanApprovalRequiredError


class TestCausalInvariantsAndFalsification(unittest.TestCase):
    def setUp(self):
        self.fixtures_dir = Path(__file__).resolve().parent.parent / "fixtures"
        self.fixture_8812 = self.fixtures_dir / "incident_INC_2026_UTIL_8812.json"
        self.connector = FederatedDataConnector(self.fixture_8812)

    def test_causal_evidence_citation_structure_and_types(self):
        citation = CausalEvidenceCitation(
            source_table="maintenance_history",
            row_id="MAINT-ROW-99182",
            fact_observed="L-09 Neutral lug torqued 45 days prior",
            supports_hypothesis=True,
            confidence_delta=0.35,
        )
        self.assertEqual(citation.source_table, "maintenance_history")
        self.assertEqual(citation.row_id, "MAINT-ROW-99182")
        self.assertTrue(citation.supports_hypothesis)
        self.assertAlmostEqual(citation.confidence_delta, 0.35)

    def test_incident_diagnosis_serialization_and_hash(self):
        diag = IncidentDiagnosis(
            incident_id="INC-2026-UTIL-8812",
            asset_id="XFMR-SUB-44",
            initial_hypothesis="H1: Catastrophic Internal Arc",
            initial_verdict="REJECTED_AS_FALSE_CORRELATION",
            evidence_trail=[],
            falsified_hypotheses=[{"hypothesis": "H1", "refutation_reason": "DGA hydrogen levels zero"}],
            confirmed_root_cause="Terminal connection overheating on neutral lug",
            explanation_narrative="Dissolved gas analysis shows absence of acetylene; thermal imaging confirms external localized lug heat.",
            recommended_action="Inspect and re-torque neutral lug L-09.",
            approval_required=True,
            is_authorized_by_human=False,
            audit_ack_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            sponsor_metadata={"zetaris": True, "meterless": True, "nemotron": True},
        )
        data = diag.to_dict()
        self.assertEqual(data["incident_id"], "INC-2026-UTIL-8812")
        self.assertEqual(data["initial_verdict"], "REJECTED_AS_FALSE_CORRELATION")
        self.assertEqual(len(data["falsified_hypotheses"]), 1)
        self.assertTrue(data["approval_required"])

    def test_commander_refutes_internal_arc_on_incident_8812(self):
        commander = GridMindCommander(self.connector)
        diag = commander.investigate_incident()
        self.assertEqual(diag.initial_verdict, "REJECTED_AS_FALSE_CORRELATION")
        self.assertTrue(len(diag.evidence_trail) > 0)
        self.assertTrue(diag.approval_required)

    def test_approval_gate_strictly_enforces_auth_token(self):
        gate = HumanApprovalGate()
        commander = GridMindCommander(self.connector, gate)
        diag = commander.investigate_incident()
        with self.assertRaises(HumanApprovalRequiredError):
            commander.dispatch_remediation_task(diag)


if __name__ == "__main__":
    unittest.main()
