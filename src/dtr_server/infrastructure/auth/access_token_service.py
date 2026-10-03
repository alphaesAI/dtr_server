import secrets
from typing import Any

from dtr_server.config import Settings


class AccessTokenService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def issue_token(self, scope: str, client_id: str) -> dict[str, Any]:
        _ = client_id
        return {
            "access_token": secrets.token_urlsafe(32),
            "token_type": "bearer",
            "expires_in": self._settings.smart_access_token_lifetime_seconds,
            "scope": scope,
        }
