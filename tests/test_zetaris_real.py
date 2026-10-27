"""Tests for the opt-in REAL Zetaris engine bridge.

* Unit tests use a fake runner and run offline everywhere ($0, no network).
* The live test runs only when a real engine is configured
  (ZETARIS_JDBC_JAR + ZETARIS_PASSWORD + java) and GRIDMIND_ZETARIS_LIVE=1; otherwise it is skipped.
"""

from __future__ import annotations

import json
import os
import subprocess
import unittest
from pathlib import Path
from unittest import mock

from src.data_connector import FederatedDataConnector
from src.sponsors.zetaris_real import (
    REAL_EXECUTION_MODE,
    ZetarisRealEngine,
    ZetarisRealEngineUnavailable,
)

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "incident_INC_2026_UTIL_8812.json"
# The real-engine synthetic dataset (integrations/zetaris/data) contains asset TR-102 == fixture 5501.
FIXTURE_TR102 = FIXTURE.with_name("incident_INC_2026_UTIL_5501.json")

FAKE_OUTPUT = {
    "statements": [
        {
            "sql": "SELECT ...",
            "columns": ["scada_row_id", "maint_row_id", "ticket_row_id"],
            "rows": [["SCADA-ROW-44012", "MNT-7002", "TKT-9001"], ["SCADA-ROW-44012", "MNT-7002", "TKT-9002"]],
            "elapsed_ms": 1234,
        }
    ]
}


def _configured_engine(tmp_path: Path) -> ZetarisRealEngine:
    jar = tmp_path / "fake.jar"
    jar.write_bytes(b"x")
    return ZetarisRealEngine(jar_path=str(jar))


class TestRealEngineBridgeOffline(unittest.TestCase):
    def setUp(self):
        import tempfile

        self.tmp = Path(tempfile.mkdtemp())

    def test_not_configured_by_default(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            eng = ZetarisRealEngine()
            self.assertFalse(eng.is_configured())
            with self.assertRaises(ZetarisRealEngineUnavailable):
                eng.incident_federation("TR-102")

    def test_default_connector_stays_on_mock(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            bundle = FederatedDataConnector(FIXTURE).execute_federated_query()
        self.assertFalse(bundle["zetaris_real"]["used"])
        self.assertEqual(bundle["zetaris_real"]["fallback"], "MOCK")
        self.assertEqual(bundle["zetaris_execution"]["execution_mode"], "LOCAL_VIRTUAL_FEDERATION")

    def test_requested_but_unavailable_falls_back_without_raising(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            bundle = FederatedDataConnector(FIXTURE, use_real_engine=True).execute_federated_query()
        self.assertFalse(bundle["zetaris_real"]["used"])
        self.assertIn("ZETARIS_JDBC_JAR", bundle["zetaris_real"]["reason"])
        self.assertTrue(bundle["scada"] is not None)  # offline pipeline intact

    def test_asset_id_injection_is_rejected(self):
        eng = _configured_engine(self.tmp)
        with self.assertRaises(ValueError):
            eng.incident_federation("TR-102' OR '1'='1")

    def test_real_path_parses_runner_output_and_keeps_password_out_of_argv(self):
        eng = _configured_engine(self.tmp)
        proc = subprocess.CompletedProcess([], 0, stdout=json.dumps(FAKE_OUTPUT).encode(), stderr=b"")
        env = {"ZETARIS_PASSWORD": "s3cret-test-value", "PATH": os.environ.get("PATH", "")}
        with mock.patch.dict(os.environ, env, clear=True), \
             mock.patch("src.sponsors.zetaris_real.shutil.which", return_value="/usr/bin/java"), \
             mock.patch("src.sponsors.zetaris_real.subprocess.run", return_value=proc) as run:
            res = eng.incident_federation("TR-102")
            argv = run.call_args.args[0]
            self.assertNotIn("s3cret-test-value", " ".join(argv))
            self.assertEqual(run.call_args.kwargs["env"]["ZETARIS_PASSWORD"], "s3cret-test-value")
            bundle = FederatedDataConnector(FIXTURE, use_real_engine=True, real_engine=eng).execute_federated_query()
        self.assertEqual(res["row_count"], 2)
        self.assertEqual(res["execution_mode"], REAL_EXECUTION_MODE)
        self.assertEqual(res["rows"][1]["ticket_row_id"], "TKT-9002")
        self.assertTrue(bundle["zetaris_real"]["used"])
        # the mock plan is still reported, clearly labelled as the mock
        self.assertEqual(bundle["zetaris_execution"]["execution_mode"], "LOCAL_VIRTUAL_FEDERATION")

    def test_engine_error_is_unavailable(self):
        eng = _configured_engine(self.tmp)
        bad = {"statements": [{"sql": "x", "error": "table not found"}]}
        proc = subprocess.CompletedProcess([], 0, stdout=json.dumps(bad).encode(), stderr=b"")
        with mock.patch.dict(os.environ, {"ZETARIS_PASSWORD": "x"}), \
             mock.patch("src.sponsors.zetaris_real.shutil.which", return_value="/usr/bin/java"), \
             mock.patch("src.sponsors.zetaris_real.subprocess.run", return_value=proc):
            with self.assertRaises(ZetarisRealEngineUnavailable):
                eng.fleet_summary()


@unittest.skipUnless(
    os.environ.get("GRIDMIND_ZETARIS_LIVE") == "1" and ZetarisRealEngine().is_configured(),
    "live Zetaris engine not configured (set GRIDMIND_ZETARIS_LIVE=1, ZETARIS_JDBC_JAR, ZETARIS_PASSWORD)",
)
class TestRealEngineLive(unittest.TestCase):
    def test_live_version_and_federated_join(self):
        eng = ZetarisRealEngine()
        self.assertIn("2.4.3.1", list(eng.server_version()["rows"][0].values()))
        res = eng.incident_federation("TR-102")
        self.assertEqual(res["row_count"], 10)
        self.assertEqual({r["maint_row_id"] for r in res["rows"]}, {"MNT-7002"})
        self.assertEqual({r["ticket_row_id"] for r in res["rows"]}, {"TKT-9001", "TKT-9002"})
        fleet = {r["asset_id"]: r for r in eng.fleet_summary()["rows"]}
        self.assertEqual(set(fleet), {"TR-102", "TR-205", "TR-310"})
        bundle = FederatedDataConnector(FIXTURE_TR102, use_real_engine=True, real_engine=eng).execute_federated_query()
        self.assertTrue(bundle["zetaris_real"]["used"])
        self.assertEqual(bundle["zetaris_real"]["asset_id"], "TR-102")
        self.assertEqual(bundle["zetaris_real"]["row_count"], 10)


if __name__ == "__main__":
    unittest.main()
