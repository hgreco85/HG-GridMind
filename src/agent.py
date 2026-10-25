"""HG GridMind — AI Incident Commander Agent Core.

Challenge 02 Track: The Agent That Can Explain Why.
Open Agent Hackathon 2026.

Integrates:
- Zetaris: Zero-ETL Virtual SQL Query Federation
- Meterless: Local Context Engines (H-MEM, Markovian, World Model)
- NVIDIA Nemotron: Multi-step Causal Reasoning & Active Falsification
- Cursor: AI-Assisted Development Tracking
- HG HumanApprovalGate: Fail-closed safety barrier for physical grid operations
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from src.data_connector import FederatedDataConnector
from src.gate import HumanApprovalGate, HumanApprovalRequiredError
from src.sponsors.cursor_audit import CursorEnvironmentAudit
from src.sponsors.meterless_adapter import MeterlessContextLayer
from src.sponsors.nemotron_adapter import NemotronCausalReasoner, CausalHypothesis


@dataclass
class CausalEvidenceCitation:
    source_table: str
    row_id: str
    fact_observed: str
    supports_hypothesis: bool
    confidence_delta: float


@dataclass
class IncidentDiagnosis:
    incident_id: str
    asset_id: str
    initial_hypothesis: str
    initial_verdict: str
    evidence_trail: List[CausalEvidenceCitation]
    falsified_hypotheses: List[Dict[str, str]]
    confirmed_root_cause: str
    explanation_narrative: str
    recommended_action: str
    approval_required: bool
    is_authorized_by_human: bool
    audit_ack_hash: str
    sponsor_metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "asset_id": self.asset_id,
            "initial_hypothesis": self.initial_hypothesis,
            "initial_verdict": self.initial_verdict,
            "evidence_trail": [asdict(e) for e in self.evidence_trail],
            "falsified_hypotheses": self.falsified_hypotheses,
            "confirmed_root_cause": self.confirmed_root_cause,
            "explanation_narrative": self.explanation_narrative,
            "recommended_action": self.recommended_action,
            "approval_required": self.approval_required,
            "is_authorized_by_human": self.is_authorized_by_human,
            "audit_ack_hash": self.audit_ack_hash,
            "sponsor_metadata": self.sponsor_metadata,
        }


class GridMindCommander:
    """Autonomous Operations Incident Commander with explainable causal reasoning."""

    def __init__(
        self,
        connector: FederatedDataConnector,
        approval_gate: Optional[HumanApprovalGate] = None,
        nemotron_engine: Optional[NemotronCausalReasoner] = None,
    ):
        self.connector = connector
        self.approval_gate = approval_gate or HumanApprovalGate()
        self.nemotron = nemotron_engine or NemotronCausalReasoner()
        self.cursor_audit = CursorEnvironmentAudit()

    def investigate_incident(self) -> IncidentDiagnosis:
        """Executes the full multi-step investigative cycle with active falsification."""
        # 1. Zetaris Zero-ETL Data Federation
        bundle = self.connector.execute_federated_query("INCIDENT_FEDERATION")
        incident_id = bundle.get("incident_id", "UNKNOWN")
        asset_id = bundle.get("asset_id", "UNKNOWN")
        init_rep = bundle.get("initial_report", {})
        initial_symptom = init_rep.get("observed_symptom", "Perturbación operativa en red eléctrica.")

        # 2. Meterless Context Layer (H-MEM timeline & World Model)
        meterless = MeterlessContextLayer(incident_id, asset_id=asset_id)
        raw_events = bundle.get("maintenance", []) + bundle.get("scada", []) + bundle.get("tickets", [])
        meterless.ingest_h_mem_timeline(raw_events)
        meterless.compute_markovian_transitions()
        world_model = meterless.build_world_model_graph()
        meterless_context = meterless.export_context_bundle()

        # 3. Dynamic Causal Evaluation via Nemotron Reasoner
        explanation = self.nemotron.generate_causal_explanation(bundle, meterless_context)
        hypotheses_raw = explanation.get("hypotheses_evaluated", [])

        # Extract citations and falsified records with deduplication
        citations: List[CausalEvidenceCitation] = []
        falsified: List[Dict[str, str]] = []
        seen_citations = set()

        for h in hypotheses_raw:
            if h.get("status") == "FALSIFIED":
                falsified.append({
                    "hypothesis": h.get("title", ""),
                    "falsified_by_citation": h.get("falsification_evidence") or "Falsified by sensor constraints",
                    "reason": h.get("physical_mechanism", ""),
                })
            elif h.get("status") == "CONFIRMED":
                for cit in h.get("supporting_citations", []):
                    table_name = "maintenance_history" if "MAINT" in cit else ("scada_telemetry" if "SCADA" in cit else "tickets_database")
                    cit_key = (table_name, cit)
                    if cit_key in seen_citations:
                        continue
                    seen_citations.add(cit_key)
                    citations.append(
                        CausalEvidenceCitation(
                            source_table=table_name,
                            row_id=cit,
                            fact_observed=f"Confirmed physical evidence: {h.get('physical_mechanism', '')[:60]}...",
                            supports_hypothesis=True,
                            confidence_delta=h.get("posterior_probability", 0.9),
                        )
                    )

        # In case no citations were built from confirmed (e.g. abstention), map evaluated rows
        if not citations:
            for s in bundle.get("scada", []):
                if not isinstance(s, dict):
                    continue
                row_id = str(s.get("row_id") or "UNKNOWN")
                cit_key = ("scada_telemetry", row_id)
                if cit_key in seen_citations:
                    continue
                seen_citations.add(cit_key)
                citations.append(
                    CausalEvidenceCitation(
                        source_table="scada_telemetry",
                        row_id=row_id,
                        fact_observed=f"SCADA current/voltage evaluated: relay flags={s.get('relay_flags')}",
                        supports_hypothesis=False,
                        confidence_delta=0.0,
                    )
                )

        confirmed_cause = explanation["confirmed_cause"]
        verdict = explanation["verdict_code"]
        narrative = explanation["narrative_explanation"]
        remediation = explanation["recommended_action"]

        # 4. Cryptographic Audit ACK (HG-GRIDMIND-ACK-V1)
        raw_seed = f"{incident_id}:{asset_id}:{confirmed_cause}:{time.time()}"
        ack_hash = hashlib.sha256(raw_seed.encode("utf-8")).hexdigest()

        sponsor_meta = {
            "zetaris": bundle.get("metadata", {}),
            "meterless": meterless_context,
            "nemotron": {
                "model": self.nemotron.model_name,
                "execution_mode": explanation.get("execution_mode"),
                "cost_usd": self.nemotron.cost_usd,
                "reasoning_steps": explanation.get("reasoning_steps", 4),
            },
            "cursor": self.cursor_audit.to_dict(),
        }

        return IncidentDiagnosis(
            incident_id=incident_id,
            asset_id=asset_id,
            initial_hypothesis=initial_symptom,
            initial_verdict=verdict,
            evidence_trail=citations,
            falsified_hypotheses=falsified,
            confirmed_root_cause=confirmed_cause,
            explanation_narrative=narrative,
            recommended_action=remediation,
            approval_required=True,
            is_authorized_by_human=self.approval_gate.is_approved(),
            audit_ack_hash=f"HG-GRIDMIND-ACK-{ack_hash[:16].upper()}",
            sponsor_metadata=sponsor_meta,
        )

    def dispatch_remediation_task(self, diagnosis: IncidentDiagnosis) -> Dict[str, Any]:
        """Dispatches physical remediation only if human approval gate is satisfied."""
        self.approval_gate.verify_or_raise(
            f"Despacho operativo de maniobra sobre {diagnosis.asset_id} para {diagnosis.incident_id}"
        )
        return {
            "status": "DISPATCHED_TO_GRID_OPERATIONS",
            "incident_id": diagnosis.incident_id,
            "asset_id": diagnosis.asset_id,
            "remediation_order": diagnosis.recommended_action,
            "authorized_by": self.approval_gate.approved_by,
            "authorization_role": self.approval_gate.role_authorized,
            "approval_token": self.approval_gate.approval_token,
            "signed_at_utc": self.approval_gate.timestamp_utc,
            "audit_trail_hash": diagnosis.audit_ack_hash,
            "spend_usd": 0.0,
        }
