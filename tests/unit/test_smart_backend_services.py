import json
import time
import uuid
from pathlib import Path

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
from fastapi.testclient import TestClient

from dtr_server.config import CLIENT_ASSERTION_TYPE, Settings, get_settings
from dtr_server.main import app
from dtr_server.presentation.api.dependencies import get_token_exchange_use_case

client = TestClient(app)

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _generate_es384_jwks() -> tuple[dict, ec.EllipticCurvePrivateKey, str]:
    private_key = ec.generate_private_key(ec.SECP384R1())
    public_key = private_key.public_key()
    kid = "test-es384-kid"

    private_numbers = private_key.private_numbers()
    public_numbers = private_numbers.public_numbers

    def int_to_b64url(value: int, length: int) -> str:
        import base64

        return base64.urlsafe_b64encode(value.to_bytes(length, "big")).decode("ascii").rstrip("=")

    jwk_public = {
        "kty": "EC",
        "crv": "P-384",
        "x": int_to_b64url(public_numbers.x, 48),
        "y": int_to_b64url(public_numbers.y, 48),
        "kid": kid,
        "alg": "ES384",
        "use": "sig",
        "key_ops": ["verify"],
    }
    return {"keys": [jwk_public]}, private_key, kid


def _make_assertion(
    private_key: ec.EllipticCurvePrivateKey,
    kid: str,
    client_id: str,
    token_url: str,
    alg: str = "ES384",
) -> str:
    now = int(time.time())
    payload = {
        "iss": client_id,
        "sub": client_id,
        "aud": token_url,
        "exp": now + 300,
        "jti": str(uuid.uuid4()),
    }
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return jwt.encode(
        payload,
        private_pem,
        algorithm=alg,
        headers={"kid": kid, "typ": "JWT", "alg": alg},
    )


def test_smart_configuration_endpoint() -> None:
    response = client.get("/fhir/.well-known/smart-configuration")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")

    config = response.json()
    settings = Settings()
    assert config["authorization_endpoint"] == settings.smart_authorization_endpoint
    assert config["token_endpoint"] == settings.smart_token_endpoint
    assert "authorization_code" in config["grant_types_supported"]
    assert "client_credentials" in config["grant_types_supported"]
    assert "S256" in config["code_challenge_methods_supported"]
    assert "plain" not in config["code_challenge_methods_supported"]
    assert "sso-openid-connect" not in config["capabilities"]
    assert "issuer" not in config


def test_token_rejects_invalid_grant_type() -> None:
    response = client.post(
        "/fhir/auth/token",
        data={
            "grant_type": "not_a_grant_type",
            "client_assertion_type": CLIENT_ASSERTION_TYPE,
            "client_assertion": "invalid",
            "scope": "system/*.rs",
        },
    )
    assert response.status_code == 400


def test_token_rejects_invalid_client_assertion_type() -> None:
    response = client.post(
        "/fhir/auth/token",
        data={
            "grant_type": "client_credentials",
            "client_assertion_type": "not_an_assertion_type",
            "client_assertion": "invalid",
            "scope": "system/*.rs",
        },
    )
    assert response.status_code in {400, 401}


def test_token_success_with_valid_client_assertion(monkeypatch) -> None:
    public_jwks, private_key, kid = _generate_es384_jwks()
    settings = Settings()
    monkeypatch.setenv("SMART_TRUSTED_JWKS_JSON", json.dumps(public_jwks))
    monkeypatch.setenv("SMART_JWKS_URLS", "")
    get_settings.cache_clear()
    get_token_exchange_use_case.cache_clear()

    assertion = _make_assertion(private_key, kid, "inferno-client", settings.smart_token_endpoint)
    response = client.post(
        "/fhir/auth/token",
        data={
            "grant_type": "client_credentials",
            "client_assertion_type": CLIENT_ASSERTION_TYPE,
            "client_assertion": assertion,
            "scope": "system/*.rs",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["token_type"].lower() == "bearer"
    assert isinstance(body["expires_in"], int)
    assert body["scope"] == "system/*.rs"
