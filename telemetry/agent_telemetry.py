import time
import math
from typing import Dict, Any, List, Optional


class TelemetryValidationError(Exception):
    """Raised when telemetry records fail validation checks."""
    pass


class LatencyBoundaryExceededError(TelemetryValidationError):
    """Raised when latency measurements exceed boundary constraints."""
    pass


class AgentTelemetryTracker:
    """Tracks and validates agent telemetry events with deterministic metrics and latency bounds."""

    def __init__(self, agent_id: str, default_latency_budget_ms: float = 500.0):
        self.agent_id = agent_id
        self.default_latency_budget_ms = default_latency_budget_ms
        self.events: List[Dict[str, Any]] = []

    def record_event(
        self,
        action: str,
        latency_ms: float,
        status: str = "success",
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
    ) -> Dict[str, Any]:
        if latency_ms < 0:
            raise TelemetryValidationError(f"Negative latency is invalid: {latency_ms} ms")
        if math.isnan(latency_ms) or math.isinf(latency_ms):
            raise TelemetryValidationError(f"Non-finite latency is invalid: {latency_ms}")
        if not action or not isinstance(action, str):
            raise TelemetryValidationError("Action must be a non-empty string")
        if status not in ("success", "failure", "timeout", "degraded"):
            raise TelemetryValidationError(f"Invalid status: {status}")

        event = {
            "agent_id": self.agent_id,
            "action": action,
            "latency_ms": float(latency_ms),
            "status": status,
            "metadata": metadata or {},
            "timestamp": timestamp if timestamp is not None else time.time(),
        }
        self.events.append(event)
        return event

    def get_latencies_for_action(self, action: Optional[str] = None) -> List[float]:
        if action is None:
            return [e["latency_ms"] for e in self.events]
        return [e["latency_ms"] for e in self.events if e["action"] == action]

    def calculate_percentile(self, percentile: float, action: Optional[str] = None) -> float:
        """Deterministic nearest-rank percentile calculation."""
        if not (0.0 <= percentile <= 100.0):
            raise ValueError(f"Percentile must be between 0 and 100, got {percentile}")
        latencies = sorted(self.get_latencies_for_action(action))
        if not latencies:
            return 0.0
        if percentile == 0.0:
            return latencies[0]
        index = math.ceil((percentile / 100.0) * len(latencies)) - 1
        index = max(0, min(index, len(latencies) - 1))
        return latencies[index]

    def assert_latency_boundaries(
        self,
        action: Optional[str] = None,
        max_allowed_ms: Optional[float] = None,
        p95_allowed_ms: Optional[float] = None,
        p99_allowed_ms: Optional[float] = None,
    ) -> None:
        """Assert that latency does not violate strict hard boundaries."""
        effective_max = max_allowed_ms if max_allowed_ms is not None else self.default_latency_budget_ms
        latencies = self.get_latencies_for_action(action)
        if not latencies:
            return

        peak_latency = max(latencies)
        if peak_latency > effective_max:
            raise LatencyBoundaryExceededError(
                f"Peak latency {peak_latency}ms exceeded maximum boundary {effective_max}ms for action '{action}'"
            )

        if p95_allowed_ms is not None:
            p95 = self.calculate_percentile(95.0, action)
            if p95 > p95_allowed_ms:
                raise LatencyBoundaryExceededError(
                    f"P95 latency {p95}ms exceeded boundary {p95_allowed_ms}ms for action '{action}'"
                )

        if p99_allowed_ms is not None:
            p99 = self.calculate_percentile(99.0, action)
            if p99 > p99_allowed_ms:
                raise LatencyBoundaryExceededError(
                    f"P99 latency {p99}ms exceeded boundary {p99_allowed_ms}ms for action '{action}'"
                )

    def validate_deterministic_schema(self, required_fields: Optional[List[str]] = None) -> bool:
        """Validate schema consistency deterministically across all tracked events."""
        fields = required_fields or ["agent_id", "action", "latency_ms", "status", "metadata", "timestamp"]
        for idx, event in enumerate(self.events):
            for field in fields:
                if field not in event:
                    raise TelemetryValidationError(f"Event index {idx} missing required field '{field}'")
            if event["agent_id"] != self.agent_id:
                raise TelemetryValidationError(
                    f"Event index {idx} agent_id mismatch: expected {self.agent_id}, got {event['agent_id']}"
                )
        return True
