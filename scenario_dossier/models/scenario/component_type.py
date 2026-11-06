from enum import Enum


class ComponentType(str, Enum):
    OVERLAYS = "overlays"
    INDICATORS = "indicators"
    MEASURES = "measures"
    ALERTS = "alerts"

    @classmethod
    def values(cls) -> tuple[str, ...]:
        return tuple(item.value for item in cls)
