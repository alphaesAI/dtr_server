from typing import Any

from src.api.infrastructure.approval_response_builder import ApprovalResponseBundleBuilder
from src.api.infrastructure.pas_request_parser import PasRequestBundleParser


class SubmitPriorAuthorization:
    """Orchestrate PAS Claim/$submit approval workflow (Inferno 2.1)."""

    def __init__(
        self,
        parser: PasRequestBundleParser,
        builder: ApprovalResponseBundleBuilder,
    ) -> None:
        self._parser = parser
        self._builder = builder

    def execute(self, bundle: dict[str, Any]) -> dict[str, Any]:
        request = self._parser.parse(bundle)
        return self._builder.build(request)
