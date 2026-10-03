from typing import Any

from dtr_server.domain.ports import CapabilityStatementProvider


class GetCapabilityStatement:
    def __init__(self, provider: CapabilityStatementProvider) -> None:
        self._provider = provider

    def execute(self, fhir_base_url: str) -> dict[str, Any]:
        return self._provider.build_instance(fhir_base_url)
