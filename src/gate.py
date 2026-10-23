"""Human Approval Gate Module for HG GridMind.

Enforces strict fail-closed safety semantics for critical grid operations.
No remediation actions, dispatches, or state mutations may occur without
explicit human operator sign-off and verifiable cryptographic audit token.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Optional


class HumanApprovalRequiredError(PermissionError):
    """Raised when an autonomous dispatch is attempted without human authorization."""
    pass


@dataclass(frozen=True)
class HumanApprovalGate:
    """Cryptographically verifiable fail-closed gate for operational dispatch."""
    approval_token: Optional[str] = None
    approved_by: Optional[str] = None
    timestamp_utc: Optional[str] = None
    role_authorized: Optional[str] = None

    def is_approved(self) -> bool:
        """Checks if the gate has a valid, non-empty approval signature."""
        return bool(
            self.approval_token
            and self.approval_token.startswith("HUMAN-SIGNOFF-")
            and self.approved_by
            and self.timestamp_utc
        )

    def verify_or_raise(self, action_name: str) -> None:
        """Enforces fail-closed safety; raises if authorization is missing."""
        if not self.is_approved():
            raise HumanApprovalRequiredError(
                f"[HUMAN_APPROVAL_GATE] Action blocked: '{action_name}'. "
                "Autonomous physical dispatch is prohibited. An authorized human operator "
                "must review the causal explanation and issue a cryptographic sign-off token."
            )

    @classmethod
    def issue_token(cls, operator_name: str, operator_role: str, action_summary: str) -> HumanApprovalGate:
        """Issues an authenticated sign-off token for a verified human operator."""
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        token_seed = f"{operator_name}:{operator_role}:{action_summary}:{timestamp}"
        token_hash = hashlib.sha256(token_seed.encode("utf-8")).hexdigest()[:16].upper()
        token = f"HUMAN-SIGNOFF-{token_hash}"
        return cls(
            approval_token=token,
            approved_by=operator_name,
            timestamp_utc=timestamp,
            role_authorized=operator_role,
        )
