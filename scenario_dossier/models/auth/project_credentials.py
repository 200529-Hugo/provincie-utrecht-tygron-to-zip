from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectCredentials:
    base_url: str
    username: str
    login_key: str
    domain: str = ""

    def __post_init__(self) -> None:
        if not self.base_url.strip():
            raise ValueError("Tygron-URL is verplicht.")
        if not self.username.strip():
            raise ValueError("Gebruikersnaam is verplicht.")
        if not self.login_key.strip():
            raise ValueError("Login key is verplicht.")
