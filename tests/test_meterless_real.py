"""Tests for the real Meterless H-MEM bridge.

Offline tests always run. The engine tests run when the engine is vendored
(``bash integrations/meterless/setup.sh``); otherwise they are skipped.
"""
import json
import tempfile
import unittest
from pathlib import Path

from src.data_connector import FederatedDataConnector
from src.sponsors.meterless_real import (
    MeterlessHMemEngine, REAL_EXECUTION_MODE, default_questions, facts_from_zetaris_rows,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_TR102 = ROOT / "fixtures" / "incident_INC_2026_UTIL_5501.json"
EVIDENCE = ROOT / "integrations" / "zetaris" / "evidence" / "04_federated.json"


def real_zetaris_rows():
    """Rows captured from the REAL Zetaris engine (evidence file), as dicts."""
    st = json.loads(EVIDENCE.read_text(encoding="utf-8"))["statements"][0]
    return [dict(zip(st["columns"], r)) for r in st["rows"]]


class FakeZetaris:
    def incident_federation(self, asset_id, neutral_threshold=15):
        return {"rows": real_zetaris_rows(), "row_count": 10, "execution_mode": "FAKE"}


class OfflineTests(unittest.TestCase):
    def test_facts_one_per_source_row_with_provenance(self):
        facts = facts_from_zetaris_rows(real_zetaris_rows(), "TR-102")
        sources = [f["source"] for f in facts]
        self.assertEqual(len(sources), len(set(sources)))
        self.assertEqual(len(facts), 5 + 1 + 2)  # 5 SCADA rows, 1 DGA row, 2 tickets
        self.assertTrue(all(s.startswith("zetaris:") for s in sources))
        self.assertIn("37.5 A", " ".join(f["content"] for f in facts))

    def test_default_off_is_labelled_mimic(self):
        c = FederatedDataConnector(FIXTURE_TR102, use_real_engine=False, use_real_meterless=False)
        out = c.execute_federated_query()["meterless_real"]
        self.assertFalse(out["used"])
        self.assertEqual(out["fallback"], "MIMIC")

    def test_requested_without_real_zetaris_rows_falls_back(self):
        c = FederatedDataConnector(FIXTURE_TR102, use_real_engine=False, use_real_meterless=True)
        out = c.execute_federated_query()["meterless_real"]
        self.assertFalse(out["used"])
        self.assertIn("no real Zetaris rows", out["reason"])

    def test_engine_unavailable_never_raises(self):
        class Broken(MeterlessHMemEngine):
            def configuration_problem(self):
                return "forced"
        c = FederatedDataConnector(
            FIXTURE_TR102, use_real_engine=True, real_engine=FakeZetaris(),
            use_real_meterless=True, meterless_engine=Broken(),
        )
        out = c.execute_federated_query()["meterless_real"]
        self.assertFalse(out["used"])
        self.assertEqual(out["reason"], "forced")

    def test_bad_feedback_rejected(self):
        eng = MeterlessHMemEngine()
        if not eng.available():
            self.skipTest("engine not vendored")
        with self.assertRaises(ValueError):
            eng.ingest_and_recall([], [], feedback="bogus")


@unittest.skipUnless(MeterlessHMemEngine().available(), "Meterless H-MEM engine not vendored (integrations/meterless/setup.sh)")
class RealEngineTests(unittest.TestCase):
    def test_real_hmem_ingest_recall_ledger_feedback(self):
        with tempfile.TemporaryDirectory() as d:
            eng = MeterlessHMemEngine(state_dir=d)
            facts = facts_from_zetaris_rows(real_zetaris_rows(), "TR-102")
            res = eng.ingest_and_recall(facts, default_questions("TR-102"))
            self.assertEqual(res["execution_mode"], REAL_EXECUTION_MODE)
            self.assertEqual(res["added"], 8)
            self.assertEqual(res["memories_total"], 8)
            dga = res["answers"][1]["memories"]
            self.assertTrue(dga, "DGA question must retrieve something")
            self.assertTrue(any("MNT-7002" in m["content"] for m in dga))
            ids = list(res["ledger"])
            self.assertTrue(ids)
            for i in ids:
                actions = [e["action"] for e in res["ledger"][i]]
                self.assertEqual(actions[0], "create")
                self.assertIn("read", actions)
            # idempotent: the same rows are not duplicated, and state persisted across processes
            res2 = eng.ingest_and_recall(facts, [default_questions("TR-102")[0]], feedback="helpful")
            self.assertEqual(res2["added"], 0)
            self.assertEqual(res2["skipped_existing"], 8)
            self.assertEqual(res2["memories_total"], 8)
            fb = [e for v in res2["ledger"].values() for e in v if e["action"] == "feedback"]
            self.assertTrue(fb, "operator feedback must be recorded in the TrustLedger")

    def test_connector_end_to_end_with_real_hmem(self):
        with tempfile.TemporaryDirectory() as d:
            c = FederatedDataConnector(
                FIXTURE_TR102, use_real_engine=True, real_engine=FakeZetaris(),
                use_real_meterless=True, meterless_engine=MeterlessHMemEngine(state_dir=d),
            )
            out = c.execute_federated_query()["meterless_real"]
            self.assertTrue(out["used"])
            self.assertEqual(out["execution_mode"], REAL_EXECUTION_MODE)
            self.assertEqual(out["memories_total"], 8)


if __name__ == "__main__":
    unittest.main()
