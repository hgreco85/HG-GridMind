"""Fail-closed checks for the offline Zetaris adapter.

These tests do not establish genuine Zetaris connectivity.
"""
import unittest

from src.sponsors.zetaris_adapter import ZetarisVirtualDataFabric


class ZetarisConnectivityGateTest(unittest.TestCase):
    def test_provider_hostname_alone_does_not_claim_cloud_connection(self):
        fabric = ZetarisVirtualDataFabric(
            endpoint_url="https://zetarishackathon.azurecr.io/unreachable"
        )
        self.assertFalse(fabric.is_cloud_connected)
        self.assertEqual(fabric.cloud_status, "BLOCKED_NO_VERIFIED_PROVIDER_CONNECTION")
        plan = fabric.explain_query_plan("INCIDENT_FEDERATION")
        self.assertEqual(plan["execution_mode"], "LOCAL_VIRTUAL_FEDERATION")
        self.assertNotEqual(plan["cloud_status"], "CONNECTED")

    def test_default_local_mode_is_not_cloud(self):
        fabric = ZetarisVirtualDataFabric()
        self.assertFalse(fabric.is_cloud_connected)
        self.assertEqual(fabric.cloud_status, "BLOCKED_NO_VERIFIED_PROVIDER_CONNECTION")


if __name__ == "__main__":
    unittest.main()
