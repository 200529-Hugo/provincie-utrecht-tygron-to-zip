from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ValidationResult:
    status: str
    checks_ok: int
    checks_failed: int
    checks: list[dict[str, Any]] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ValidationResult":
        return cls(
            status=str(value.get("status", "afgekeurd")),
            checks_ok=int(value.get("checks_ok", 0)),
            checks_failed=int(value.get("checks_failed", 0)),
            checks=list(value.get("checks") or []),
            details=dict(value),
        )

    @property
    def approved(self) -> bool:
        return self.status == "goedgekeurd"

    def to_dict(self) -> dict[str, Any]:
        return dict(self.details)
