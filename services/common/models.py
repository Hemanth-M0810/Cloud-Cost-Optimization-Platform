from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Violation:
    violation_id: str
    policy_id: str
    subscription_id: str
    resource_id: str
    resource_group: str
    owner_email: str
    remediation_type: str
    recommended_sku: Optional[str]
    estimated_monthly_savings_usd: float
    status: str
    detected_at_utc: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ApprovalRecord:
    violation_id: str
    decision: str
    decided_by: str
    decided_at_utc: str

    @staticmethod
    def create(violation_id: str, decision: str, decided_by: str) -> "ApprovalRecord":
        return ApprovalRecord(
            violation_id=violation_id,
            decision=decision,
            decided_by=decided_by,
            decided_at_utc=datetime.utcnow().isoformat() + "Z",
        )


@dataclass
class ApprovalResourceCandidate:
    violation_id: str
    resource_id: str
    remediation_type: str
    recommended_sku: Optional[str]
    estimated_monthly_savings_usd: float
    selected_for_remediation: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ApprovalWindow:
    owner_email: str
    started_at_utc: str
    window_end_utc: str
    resources: list[ApprovalResourceCandidate]

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["resources"] = [r.to_dict() for r in self.resources]
        return payload
