from dataclasses import dataclass
from typing import Any

from dtr_server.config import BACKEND_SERVICES_GRANT_TYPE, CLIENT_ASSERTION_TYPE, Settings
from dtr_server.domain.ports import BackendServicesTokenIssuer
from dtr_server.infrastructure.auth.client_assertion_validator import (
    ClientAssertionValidationError,
    ClientAssertionValidator,
)


@dataclass(frozen=True)
class TokenRequest:
    grant_type: str | None
    client_assertion_type: str | None
    client_assertion: str | None
    scope: str | None


class OAuthError(Exception):
    def __init__(self, error: str, description: str, status_code: int) -> None:
        self.error = error
        self.description = description
        self.status_code = status_code
        super().__init__(description)


class ExchangeBackendServicesToken:
    def __init__(
        self,
        settings: Settings,
        validator: ClientAssertionValidator,
        issuer: BackendServicesTokenIssuer,
    ) -> None:
        self._settings = settings
        self._validator = validator
        self._issuer = issuer

    def execute(self, request: TokenRequest) -> dict[str, Any]:
        if request.grant_type != BACKEND_SERVICES_GRANT_TYPE:
            raise OAuthError(
                "unsupported_grant_type",
                "grant_type must be client_credentials",
                400,
            )

        if request.client_assertion_type != CLIENT_ASSERTION_TYPE:
            raise OAuthError(
                "invalid_client",
                "client_assertion_type must be urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                401,
            )

        if not request.client_assertion:
            raise OAuthError("invalid_request", "client_assertion is required", 400)

        try:
            client_id = self._validator.validate(
                request.client_assertion,
                expected_audience=self._settings.smart_token_endpoint,
            )
        except ClientAssertionValidationError as exc:
            raise OAuthError("invalid_client", str(exc), 401) from exc

        scope = (request.scope or self._settings.smart_default_scope).strip()
        return self._issuer.issue_token(scope=scope, client_id=client_id)
