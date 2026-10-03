import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

CLIENT_ASSERTION_TYPE = "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
BACKEND_SERVICES_GRANT_TYPE = "client_credentials"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    public_fhir_base_url: str = "https://manlike-blade-trilogy.ngrok-free.dev/fhir"
    server_name: str = "DTR Payer Server"
    host: str = "0.0.0.0"
    port: int = 8000

    smart_authorize_path: str = "/auth/authorize"
    smart_token_path: str = "/auth/token"
    smart_access_token_lifetime_seconds: int = 300
    smart_default_scope: str = "system/*.rs"
    smart_trusted_jwks_path: str | None = None
    smart_trusted_jwks_json: str | None = None
    smart_jwks_urls: str = (
        "https://inferno.healthit.gov/suites/custom/smart_stu2/.well-known/jwks.json"
    )
    smart_jwks_cache_seconds: int = 300
    smart_jwks_fetch_optional: bool = True
    smart_allow_unverified_client_assertion: bool = False
    smart_extra_token_audiences: str = ""

    @field_validator("public_fhir_base_url")
    @classmethod
    def strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")

    @property
    def smart_authorization_endpoint(self) -> str:
        return f"{self.public_fhir_base_url}{self.smart_authorize_path}"

    @property
    def smart_token_endpoint(self) -> str:
        return f"{self.public_fhir_base_url}{self.smart_token_path}"

    def load_trusted_jwks(self) -> dict[str, Any]:
        if self.smart_trusted_jwks_json:
            return json.loads(self.smart_trusted_jwks_json)
        if self.smart_trusted_jwks_path:
            path = Path(self.smart_trusted_jwks_path)
            return json.loads(path.read_text(encoding="utf-8"))
        default_path = Path(__file__).resolve().parent / "infrastructure" / "auth" / "trusted_jwks.json"
        if default_path.is_file():
            return json.loads(default_path.read_text(encoding="utf-8"))
        return {"keys": []}

    @property
    def smart_jwks_url_list(self) -> list[str]:
        return [url.strip() for url in self.smart_jwks_urls.split(",") if url.strip()]

    @property
    def smart_extra_audience_list(self) -> list[str]:
        return [aud.strip() for aud in self.smart_extra_token_audiences.split(",") if aud.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
