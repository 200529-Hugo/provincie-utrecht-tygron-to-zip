from dataclasses import dataclass
from typing import Any

from ..base import JsonModel


@dataclass(frozen=True)
class ComponentCountsResponse(JsonModel):
    overlays: int
    indicators: int
    measures: int
    alerts: int


@dataclass(frozen=True)
class ScenarioItemResponse(JsonModel):
    key: str
    component: str
    name: str
    detail: str
    spatial: bool
    geometry_type: str

    @classmethod
    def from_item(cls, item) -> 'ScenarioItemResponse':
        return cls(**item.to_dict())


@dataclass(frozen=True)
class PreviewFeatureResponse(JsonModel):
    component: str
    key: str
    feature: dict[str, Any]


@dataclass(frozen=True)
class InspectResponse(JsonModel):
    project: str
    scenario: str
    counts: ComponentCountsResponse
    spatial: int
    warnings: list[str]
    preview: list[PreviewFeatureResponse]
    items: list[ScenarioItemResponse]


@dataclass(frozen=True)
class RecordMetadataResponse(JsonModel):
    reference: str
    owner: str
    author: str
    classification: str
    retention_period: str


@dataclass(frozen=True)
class DecisionMetadataResponse(JsonModel):
    date: str
    status: str
    selected_scenario: str
    alternatives: str
    rationale: str


@dataclass(frozen=True)
class ArchiveSummaryResponse(JsonModel):
    schema: str
    project: str
    scenario: str
    exported_at: str
    source: str
    crs: str
    components: ComponentCountsResponse
    notes: str
    record: RecordMetadataResponse
    decision: DecisionMetadataResponse
    software: str
    token_archived: bool
    warnings: list[str]
    validation: str
    size: int

    @classmethod
    def from_metadata(cls, metadata: dict) -> 'ArchiveSummaryResponse':
        values = {name: metadata[name] for name in cls.__dataclass_fields__}
        values.update(components=ComponentCountsResponse(**metadata['components']),
                      record=RecordMetadataResponse(**metadata['record']),
                      decision=DecisionMetadataResponse(**metadata['decision']))
        return cls(**values)


@dataclass(frozen=True)
class ExportResponse(JsonModel):
    filename: str
    download: str
    summary: ArchiveSummaryResponse
    ok: bool = True
