from dataclasses import dataclass
from typing import ClassVar

from ..base import JsonModel
from .common import ImageResponse


@dataclass(frozen=True)
class ProjectResponse(JsonModel):
    file_name: str
    name: str
    active_version: int
    versions: list[str]
    description: str
    domain: str
    revision: str

    @classmethod
    def from_project(cls, project) -> 'ProjectResponse':
        return cls(**project.to_dict())


@dataclass(frozen=True)
class ProjectsResponse(JsonModel):
    projects: list[ProjectResponse]


@dataclass(frozen=True)
class DemoScenarioResponse(JsonModel):
    id: str
    name: str
    description: str

    @classmethod
    def from_scenario(cls, scenario) -> 'DemoScenarioResponse':
        return cls(id=scenario.id, name=scenario.name, description=scenario.description)


@dataclass(frozen=True)
class DemoProjectResponse(JsonModel):
    id: str
    name: str
    scenarios: list[DemoScenarioResponse]

    @classmethod
    def from_project(cls, project) -> 'DemoProjectResponse':
        return cls(id=project.id, name=project.name,
                   scenarios=[DemoScenarioResponse.from_scenario(item) for item in project.scenarios])


@dataclass(frozen=True)
class DemoCatalogResponse(JsonModel):
    projects: list[DemoProjectResponse]


@dataclass(frozen=True)
class DemoProjectsResponse(DemoCatalogResponse):
    root_field: ClassVar[str] = 'projects'


@dataclass(frozen=True)
class DemoScenariosResponse(JsonModel):
    scenarios: list[DemoScenarioResponse]
    root_field: ClassVar[str] = 'scenarios'


@dataclass(frozen=True)
class ProjectThumbnailResponse(ImageResponse):
    pass


@dataclass(frozen=True)
class DemoThumbnailResponse(ImageResponse):
    pass
