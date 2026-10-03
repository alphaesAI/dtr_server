from unittest.mock import MagicMock, patch

from dtr_server.config import Settings
from dtr_server.infrastructure.auth.jwks_resolver import JwksResolver, merge_jwks


def test_merge_jwks_skips_private_key_material() -> None:
    public = {"kid": "a", "kty": "EC", "crv": "P-384", "x": "x", "y": "y"}
    private = {**public, "d": "secret"}
    merged = merge_jwks({"keys": [private]}, {"keys": [public]})
    assert len(merged["keys"]) == 1
    assert "d" not in merged["keys"][0]


def test_resolver_fetches_remote_jwks() -> None:
    settings = Settings(
        smart_trusted_jwks_json='{"keys":[]}',
        smart_jwks_urls="https://example.com/jwks.json",
        smart_jwks_fetch_optional=False,
    )
    resolver = JwksResolver(settings)
    remote = {
        "keys": [
            {
                "kid": "inferno-kid",
                "kty": "EC",
                "crv": "P-384",
                "x": "x",
                "y": "y",
                "alg": "ES384",
            }
        ]
    }
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = remote

    with patch("dtr_server.infrastructure.auth.jwks_resolver.httpx.get", return_value=mock_response):
        jwks = resolver.resolve()

    assert jwks["keys"][0]["kid"] == "inferno-kid"
