from typing import Any, Protocol


class CapabilityStatementProvider(Protocol):
    def build_instance(self, fhir_base_url: str) -> dict[str, Any]:
        """Return a FHIR CapabilityStatement resource (instance kind)."""
        ...


class SmartConfigurationProvider(Protocol):
    def build(self) -> dict[str, Any]:
        """Return SMART /.well-known/smart-configuration JSON."""
        ...


class BackendServicesTokenIssuer(Protocol):
    def issue_token(self, scope: str, client_id: str) -> dict[str, Any]:
        """Return OAuth token response body for a validated client."""
        ...
