from typing import Any

from dtr_server.config import Settings


class BuildSmartConfiguration:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def execute(self) -> dict[str, Any]:
        return {
            "authorization_endpoint": self._settings.smart_authorization_endpoint,
            "token_endpoint": self._settings.smart_token_endpoint,
            "capabilities": [
                "client-confidential-asymmetric",
            ],
            "grant_types_supported": [
                "authorization_code",
                "client_credentials",
            ],
            "code_challenge_methods_supported": ["S256"],
        }
