from typing import Any

from fastapi import APIRouter

from src.api.config import public_fhir_base_url
from src.api.domain.errors import InvalidPasRequestError
from src.api.infrastructure.approval_response_builder import ApprovalResponseBundleBuilder
from src.api.infrastructure.fhir_responses import fhir_json_response, operation_outcome
from src.api.infrastructure.pas_request_parser import PasRequestBundleParser
from src.api.use_cases.submit_prior_authorization import SubmitPriorAuthorization

router = APIRouter(tags=["Claim"])


def _use_case() -> SubmitPriorAuthorization:
    return SubmitPriorAuthorization(
        parser=PasRequestBundleParser(),
        builder=ApprovalResponseBundleBuilder(public_fhir_base_url()),
    )


@router.post("/Claim/$submit")
async def submit_claim(payload: dict[str, Any]) -> Any:
    """PAS Claim $submit — return an approved PAS Response Bundle."""
    try:
        response_bundle = _use_case().execute(payload)
    except InvalidPasRequestError as exc:
        return fhir_json_response(
            operation_outcome(exc.message),
            status_code=400,
        )
    return fhir_json_response(response_bundle, status_code=200)
