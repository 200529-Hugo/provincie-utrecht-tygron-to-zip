from dataclasses import dataclass, field


@dataclass(frozen=True)
class ActiveSessionCredentials:
    base_url: str
    token: str = field(repr=False)

    def __post_init__(self) -> None:
        if not self.base_url.strip():
            raise ValueError("Tygron-URL is verplicht.")
        if not self.token.strip():
            raise ValueError("API-token is verplicht.")
