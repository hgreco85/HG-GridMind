import unittest
from telemetry.agent_telemetry import (
    AgentTelemetryTracker,
    TelemetryValidationError,
    LatencyBoundaryExceededError,
)


class TestAgentTelemetryHardening(unittest.TestCase):
    def setUp(self):
        self.tracker = AgentTelemetryTracker(agent_id="agent-alpha-42", default_latency_budget_ms=250.0)

    def test_deterministic_telemetry_schema_validation(self):
        """Verify strict schema structure and deterministic validation against tampering."""
        for i in range(10):
            self.tracker.record_event(
                action="query_tool",
                latency_ms=10.0 + i * 5,
                status="success",
                metadata={"iteration": i},
                timestamp=1700000000.0 + i,
            )

        self.assertTrue(self.tracker.validate_deterministic_schema())

        # Artificially inject an invalid event missing a required field
        self.tracker.events.append({"action": "orphan_action", "latency_ms": 5.0})
        with self.assertRaises(TelemetryValidationError):
            self.tracker.validate_deterministic_schema()

    def test_latency_boundary_assertions_pass(self):
        """Verify that normal deterministic latencies within limits pass boundary checks."""
        # Pre-calculated deterministic distribution
        latencies = [15.0, 20.0, 22.0, 30.0, 45.0, 60.0, 90.0, 110.0, 140.0, 180.0]
        for lat in latencies:
            self.tracker.record_event("inference", latency_ms=lat, timestamp=1700000100.0)

        # Assert with valid boundaries
        self.tracker.assert_latency_boundaries(
            action="inference",
            max_allowed_ms=200.0,
            p95_allowed_ms=190.0,
            p99_allowed_ms=200.0,
        )

        p95 = self.tracker.calculate_percentile(95.0, action="inference")
        self.assertEqual(p95, 180.0)

    def test_latency_boundary_exceeded_violations(self):
        """Ensure violating max latency or percentiles strictly triggers LatencyBoundaryExceededError."""
        for lat in [50.0, 75.0, 120.0, 300.0]:
            self.tracker.record_event("call_api", latency_ms=lat)

        # Peak (300.0ms) exceeds default budget (250.0ms)
        with self.assertRaises(LatencyBoundaryExceededError) as ctx:
            self.tracker.assert_latency_boundaries(action="call_api")
        self.assertIn("exceeded maximum boundary", str(ctx.exception))

        # Test P95 boundary violation
        with self.assertRaises(LatencyBoundaryExceededError):
            self.tracker.assert_latency_boundaries(
                action="call_api",
                max_allowed_ms=500.0,
                p95_allowed_ms=100.0,
            )

    def test_invalid_telemetry_payload_rejection(self):
        """Verify boundary rejection of negative and non-finite latencies and invalid inputs."""
        with self.assertRaises(TelemetryValidationError):
            self.tracker.record_event("step", latency_ms=-5.0)

        with self.assertRaises(TelemetryValidationError):
            self.tracker.record_event("step", latency_ms=float("nan"))

        with self.assertRaises(TelemetryValidationError):
            self.tracker.record_event("", latency_ms=10.0)

        with self.assertRaises(TelemetryValidationError):
            self.tracker.record_event("step", latency_ms=10.0, status="invalid_status")


if __name__ == "__main__":
    unittest.main()
