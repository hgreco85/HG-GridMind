import sys
import json
from pathlib import Path
from src.agent import GridMindCommander
from src.data_connector import FederatedDataConnector
from src.gate import HumanApprovalGate
from src.sponsors.nemotron_adapter import NemotronCausalReasoner

class MockConnector:
    def __init__(self, data):
        self._data = data
    def execute_federated_query(self, query_intent="INCIDENT_FEDERATION"):
        sources = self._data.get("synthetic_sources", {})
        tickets = sources.get("tickets_database", []) if sources else []
        maintenance = sources.get("maintenance_history", []) if sources else []
        scada = sources.get("scada_telemetry", []) if sources else []
        if tickets is None: tickets = []
        if maintenance is None: maintenance = []
        if scada is None: scada = []
        return {
            "incident_id": self._data.get("incident_id", "ADV-TEST"),
            "asset_id": self._data.get("asset_id", "ADV-ASSET"),
            "initial_report": self._data.get("initial_operator_report", {}),
            "tickets": tickets,
            "maintenance": maintenance,
            "scada": scada,
            "synthetic_sources": sources,
            "metadata": {"test": True}
        }

def run_test(name, payload):
    print(f"\n--- TEST: {name} ---")
    conn = MockConnector(payload)
    commander = GridMindCommander(connector=conn)
    try:
        diagnosis = commander.investigate_incident()
        print(f"RESULT: PASS/GRACEFUL")
        print(f"  Verdict: {diagnosis.initial_verdict}")
        print(f"  Confirmed Root Cause: {diagnosis.confirmed_root_cause[:80]}...")
        print(f"  Falsified Count: {len(diagnosis.falsified_hypotheses)}")
        print(f"  Citations Count: {len(diagnosis.evidence_trail)}")
        return "PASS", diagnosis.initial_verdict
    except Exception as e:
        print(f"RESULT: FAIL / CRASH ({type(e).__name__}): {e}")
        return "FAIL", f"{type(e).__name__}: {e}"

results = {}

# 1. Missing or Null Data
p1 = {
    "incident_id": "ADV-01",
    "asset_id": "TR-NULL",
    "synthetic_sources": {
        "scada_telemetry": [{"row_id": "S1", "current_phase_a_amps": None, "relay_flags": None}],
        "maintenance_history": [{"row_id": "M1", "action": None, "result_status": None}],
        "tickets_database": None
    }
}
results["1_missing_or_null"] = run_test("1. Missing or Null Data", p1)

# 2. Out-of-order records
p2 = {
    "incident_id": "ADV-02",
    "asset_id": "TR-ORDER",
    "synthetic_sources": {
        "scada_telemetry": [
            {"row_id": "S2", "timestamp": "2026-10-22T10:00:00Z", "current_phase_a_amps": 200, "current_phase_b_amps": 450, "neutral_current_amps": 200, "relay_flags": []},
            {"row_id": "S1", "timestamp": "2026-10-20T10:00:00Z", "current_phase_a_amps": 200, "current_phase_b_amps": 200, "neutral_current_amps": 0, "relay_flags": []}
        ],
        "maintenance_history": [
            {"row_id": "M2", "action": "Termografia", "result_status": "WARNING", "timestamp": "2026-10-21T00:00:00Z"},
            {"row_id": "M1", "action": "DGA cromatografia", "result_status": "NORMAL", "timestamp": "2026-10-19T00:00:00Z"}
        ]
    }
}
results["2_out_of_order"] = run_test("2. Out of order records", p2)

# 3. Inconsistent timestamps
p3 = {
    "incident_id": "ADV-03",
    "asset_id": "TR-TIME",
    "synthetic_sources": {
        "scada_telemetry": [
            {"row_id": "S1", "timestamp": None, "current_phase_a_amps": 100, "current_phase_b_amps": 100, "neutral_current_amps": 0, "relay_flags": []},
            {"row_id": "S2", "timestamp": "INVALID_DATE_FORMAT_99999", "current_phase_a_amps": 100, "current_phase_b_amps": 100, "neutral_current_amps": 0, "relay_flags": []}
        ],
        "maintenance_history": [
            {"row_id": "M1", "timestamp": "1970-01-01T00:00:00Z", "action": "DGA", "result_status": "NORMAL"}
        ]
    }
}
results["3_inconsistent_timestamps"] = run_test("3. Inconsistent timestamps", p3)

# 4. Contradictory measurements
p4 = {
    "incident_id": "ADV-04",
    "asset_id": "TR-CONTRADICTION",
    "synthetic_sources": {
        "scada_telemetry": [
            {"row_id": "S1", "current_phase_a_amps": 2000, "current_phase_b_amps": 2000, "current_phase_c_amps": 2000, "neutral_current_amps": 500, "relay_flags": ["BUCHHOLZ_TRIP", "FEEDER_50P_TRIP"]}
        ],
        "maintenance_history": [
            {"row_id": "M1", "action": "DGA cromatografia", "result_status": "CRITICAL_ALARM", "details": "Acetylene 50ppm"},
            {"row_id": "M2", "action": "DGA cromatografia", "result_status": "NORMAL", "details": "Acetylene 0.1ppm"},
            {"row_id": "M3", "action": "Termografia infrarroja", "result_status": "WARNING"}
        ]
    }
}
results["4_contradictory_measurements"] = run_test("4. Contradictory measurements", p4)

# 5. Mistyped fields
p5 = {
    "incident_id": "ADV-05",
    "asset_id": "TR-TYPES",
    "synthetic_sources": {
        "scada_telemetry": [
            {"row_id": "S1", "current_phase_a_amps": "210.4", "current_phase_b_amps": "445.8", "current_phase_c_amps": "195.2", "neutral_current_amps": "268.1", "relay_flags": "NOT_A_LIST"}
        ],
        "maintenance_history": [
            {"row_id": "M1", "action": 12345, "result_status": ["NORMAL"]}
        ]
    }
}
results["5_mistyped_fields"] = run_test("5. Mistyped fields", p5)

# 6. Irrelevant events
p6 = {
    "incident_id": "ADV-06",
    "asset_id": "TR-NOISE",
    "synthetic_sources": {
        "scada_telemetry": [
            {"row_id": "S_NOISE", "event": "Substation door opened", "temperature_ambient": 22.1, "current_phase_a_amps": 50, "current_phase_b_amps": 50, "current_phase_c_amps": 50, "neutral_current_amps": 0, "relay_flags": []}
        ],
        "maintenance_history": [
            {"row_id": "M_NOISE", "action": "Lawn mowing around fence", "result_status": "COMPLETED"}
        ],
        "tickets_database": [
            {"row_id": "T_NOISE", "description": "Streetlight bulb flickered on 4th street"}
        ]
    }
}
results["6_irrelevant_events"] = run_test("6. Irrelevant events", p6)

# 7. Duplicate IDs and nonexistent evidence
p7 = {
    "incident_id": "ADV-07",
    "asset_id": "TR-DUPES",
    "synthetic_sources": {
        "scada_telemetry": [
            {"row_id": "DUP-01", "current_phase_a_amps": 200, "current_phase_b_amps": 400, "neutral_current_amps": 200, "relay_flags": []},
            {"row_id": "DUP-01", "current_phase_a_amps": 10, "current_phase_b_amps": 10, "neutral_current_amps": 0, "relay_flags": []}
        ],
        "maintenance_history": [
            {"row_id": "DUP-01", "action": "Termografia", "result_status": "WARNING"},
            {"row_id": "DUP-01", "action": "DGA", "result_status": "NORMAL"}
        ]
    }
}
results["7_duplicate_ids"] = run_test("7. Duplicate IDs and nonexistent evidence", p7)

# 8. Out-of-domain input
p8 = {
    "incident_id": "ADV-08",
    "asset_id": "PATIENT-994",
    "domain": "HEALTHCARE",
    "synthetic_sources": {
        "scada_telemetry": [
            {"row_id": "HR-01", "heart_rate": 72, "blood_pressure": "120/80"}
        ],
        "maintenance_history": [
            {"row_id": "MED-01", "action": "Blood test", "cholesterol": 190}
        ]
    }
}
results["8_out_of_domain"] = run_test("8. Out of domain input", p8)

print("\n" + "="*50)
print("ADVERSARIAL SUMMARY:")
for k, v in results.items():
    print(f"  {k}: {v[0]} ({v[1]})")
print("="*50)
