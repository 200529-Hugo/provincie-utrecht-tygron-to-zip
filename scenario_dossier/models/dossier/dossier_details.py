from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class DossierDetails:
    reference: str = ""
    owner: str = ""
    author: str = ""
    decision_date: str = ""
    decision_status: str = ""
    alternatives: str = ""
    classification: str = ""
    retention_period: str = ""

    @classmethod
    def from_dict(cls, value: dict[str, Any] | None) -> "DossierDetails":
        source = value or {}
        return cls(**{
            field: str(source.get(field, "")).strip()[:2000]
            for field in cls.__dataclass_fields__
        })

    def to_dict(self) -> dict[str, str]:
        return asdict(self)
