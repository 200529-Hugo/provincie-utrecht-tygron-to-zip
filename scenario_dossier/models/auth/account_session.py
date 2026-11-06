from dataclasses import dataclass, field

from .project_credentials import ProjectCredentials


@dataclass
class AccountSession:
    credentials: ProjectCredentials = field(repr=False)
    expires_at: float
    projects: dict = field(default_factory=dict)
