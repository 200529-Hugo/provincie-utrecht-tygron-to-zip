from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TygronProject:
    file_name: str
    name: str
    active_version: str
    description: str = ""
    domain: str = ""
    revision: str = ""

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
        return cls(file_name=file_name, name=name, active_version=active_version,
                   description=str(value.get("description") or ""),
                   domain=str(value.get("domain") or value.get("domainName") or ""),
                   revision=str(value.get("lastActivity") or ""))

    def to_dict(self) -> dict:
        return {
            "file_name": self.file_name,
            "name": self.name,
            "active_version": 0,
            "versions": [self.active_version],
            "description": self.description,
            "domain": self.domain,
            "revision": self.revision,
        }
