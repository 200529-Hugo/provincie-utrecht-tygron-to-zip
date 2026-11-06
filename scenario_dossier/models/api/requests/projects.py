from dataclasses import dataclass, field

from ..base import EmptyRequest, JsonModel, object_value, text


@dataclass(frozen=True)
class AccountProjectsRequest(EmptyRequest):
    pass


@dataclass(frozen=True)
class LegacyProjectsRequest(JsonModel):
    base_url: str
    username: str
    login_key: str = field(repr=False)
    domain: str = ''

    @classmethod
    def from_dict(cls, value: dict) -> 'LegacyProjectsRequest':
        data = object_value(value)
        return cls(**{name: text(data, name) for name in ('base_url', 'username', 'login_key', 'domain')})


@dataclass(frozen=True)
class ProjectThumbnailRequest(JsonModel):
    project_file: str

    @classmethod
    def from_dict(cls, value: dict) -> 'ProjectThumbnailRequest':
        return cls(project_file=text(object_value(value), 'project_file'))


@dataclass(frozen=True)
class DemoCatalogRequest(EmptyRequest):
    pass


@dataclass(frozen=True)
class DemoProjectsRequest(EmptyRequest):
    pass


@dataclass(frozen=True)
class DemoProjectRequest(JsonModel):
    project_id: str

    @classmethod
    def from_dict(cls, value: dict):
        return cls(project_id=text(object_value(value), 'project_id'))


@dataclass(frozen=True)
class DemoScenariosRequest(DemoProjectRequest):
    pass


@dataclass(frozen=True)
class DemoThumbnailRequest(DemoProjectRequest):
    pass
