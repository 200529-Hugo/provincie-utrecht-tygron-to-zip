from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TygronProject:
    file_name: str
    name: str
    active_version: str

    @classmethod
    def from_api(cls, value: dict[str, Any]) -> "TygronProject":
        file_name = str(value.get("fileName") or value.get("filename") or value.get("name") or "")
        name = str(value.get("name") or value.get("displayName") or file_name)
        versions = value.get("versions") or ["Actieve versie"]
        try:
            active_index = int(value.get("activeVersion", 0))
        except (TypeError, ValueError):
            active_index = 0
        active_version = (
            str(versions[active_index])
            if 0 <= active_index < len(versions)
            else "Actieve versie"
        )
        return cls(file_name=file_name, name=name, active_version=active_version)

    def to_dict(self) -> dict[str, str]:
        return {
            "file_name": self.file_name,
            "name": self.name,
            "active_version": self.active_version,
        }
