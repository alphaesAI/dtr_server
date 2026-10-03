import time
from typing import Any

import jwt
from jwt import PyJWKSet

from dtr_server.infrastructure.auth.jwks_resolver import JwksResolver


class ClientAssertionValidationError(Exception):
    pass


class ClientAssertionValidator:
    def __init__(
        self,
        jwks_resolver: JwksResolver,
        max_future_skew_seconds: int = 300,
        allow_unverified_signature: bool = False,
        accepted_audiences: list[str] | None = None,
    ) -> None:
        self._jwks_resolver = jwks_resolver
        self._max_future_skew_seconds = max_future_skew_seconds
        self._allow_unverified_signature = allow_unverified_signature
        self._accepted_audiences = accepted_audiences or []

    def validate(self, assertion: str, expected_audience: str) -> str:
        audiences = self._audience_candidates(expected_audience)
        if self._allow_unverified_signature:
            return self._validate_unverified(assertion, audiences)

        jwks = self._jwks_resolver.resolve()
        keys = jwks.get("keys") or []
        jwk_set = PyJWKSet.from_dict(jwks) if keys else None

        try:
            header = jwt.get_unverified_header(assertion)
        except jwt.PyJWTError as exc:
            raise ClientAssertionValidationError(f"Invalid client_assertion JWT: {exc}") from exc

        signing_jwk = self._find_signing_key(jwk_set, header.get("kid"))
        algorithm = header.get("alg") or signing_jwk.algorithm_name

        last_error: Exception | None = None
        for audience in audiences:
            try:
                payload = jwt.decode(
                    assertion,
                    signing_jwk.key,
                    algorithms=[algorithm],
                    audience=audience,
                    options={"require": ["exp", "iss", "sub", "aud", "jti"]},
                )
                return self._validate_claims(payload)
            except jwt.PyJWTError as exc:
                last_error = exc
                continue

        message = f"Invalid client_assertion JWT: {last_error}" if last_error else "Invalid client_assertion JWT"
        raise ClientAssertionValidationError(message)

    def _validate_unverified(self, assertion: str, audiences: list[str]) -> str:
        try:
            payload = jwt.decode(
                assertion,
                options={
                    "verify_signature": False,
                    "require": ["exp", "iss", "sub", "aud", "jti"],
                },
            )
        except jwt.PyJWTError as exc:
            raise ClientAssertionValidationError(f"Invalid client_assertion JWT: {exc}") from exc

        token_aud = payload.get("aud")
        if isinstance(token_aud, list):
            aud_ok = any(aud in audiences for aud in token_aud)
        else:
            aud_ok = token_aud in audiences
        if not aud_ok:
            raise ClientAssertionValidationError("JWT aud does not match token endpoint")

        return self._validate_claims(payload)

    def _validate_claims(self, payload: dict[str, Any]) -> str:
        iss = payload.get("iss")
        sub = payload.get("sub")
        if not iss or not sub or iss != sub:
            raise ClientAssertionValidationError("JWT iss and sub must match and be present")

        exp = int(payload["exp"])
        now = int(time.time())
        if exp < now:
            raise ClientAssertionValidationError("JWT is expired")
        if exp > now + self._max_future_skew_seconds:
            raise ClientAssertionValidationError("JWT exp must be within five minutes")

        return str(iss)

    def _audience_candidates(self, expected_audience: str) -> list[str]:
        candidates = [expected_audience.rstrip("/"), expected_audience]
        for audience in self._accepted_audiences:
            candidates.append(audience.rstrip("/"))
            candidates.append(audience)
        return list(dict.fromkeys(candidates))

    def _find_signing_key(self, jwk_set: PyJWKSet | None, kid: str | None) -> Any:
        if jwk_set is None:
            raise ClientAssertionValidationError("No trusted JWKS keys configured")

        keys = list(jwk_set.keys)
        if not keys:
            raise ClientAssertionValidationError("No trusted JWKS keys configured")

        if kid:
            for key in keys:
                if key.key_id == kid:
                    return key
            raise ClientAssertionValidationError(f"No trusted key found for kid={kid}")

        if len(keys) == 1:
            return keys[0]

        raise ClientAssertionValidationError("JWT header kid is required when multiple keys are configured")
