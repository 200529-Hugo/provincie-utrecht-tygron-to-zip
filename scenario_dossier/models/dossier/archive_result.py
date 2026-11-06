from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ArchiveResult:
    path: Path
    metadata: dict[str, Any]

    @property
    def filename(self) -> str:
        return self.path.name

    @property
    def size(self) -> int:
        stored_size = self.metadata.get("size")
        return int(stored_size) if stored_size is not None else self.path.stat().st_size
