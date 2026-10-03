from fastapi import APIRouter, Depends

from dtr_server.application.get_capability_statement import GetCapabilityStatement
from dtr_server.config import Settings
from dtr_server.infrastructure.fhir.responses import operation_outcome_not_implemented
from dtr_server.presentation.api.dependencies import (
    get_app_settings,
    get_capability_statement_use_case,
)
from dtr_server.presentation.fhir_responses import fhir_json_response

router = APIRouter()


@router.get("/metadata")
def get_metadata(
    use_case: GetCapabilityStatement = Depends(get_capability_statement_use_case),
    settings: Settings = Depends(get_app_settings),
) -> object:
    resource = use_case.execute(settings.public_fhir_base_url)
    return fhir_json_response(resource)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/Questionnaire/$questionnaire-package")
def questionnaire_package_not_implemented() -> object:
    return fhir_json_response(
        operation_outcome_not_implemented(
            "Questionnaire/$questionnaire-package is not implemented yet."
        ),
        status_code=501,
    )


@router.post("/Questionnaire/$next-question")
def next_question_not_implemented() -> object:
    return fhir_json_response(
        operation_outcome_not_implemented("Questionnaire/$next-question is not implemented yet."),
        status_code=501,
    )


@router.post("/Questionnaire/$log-questionnaire-errors")
def log_questionnaire_errors_not_implemented() -> object:
    return fhir_json_response(
        operation_outcome_not_implemented(
            "Questionnaire/$log-questionnaire-errors is not implemented yet."
        ),
        status_code=501,
    )


@router.post("/ValueSet/$expand")
def value_set_expand_not_implemented() -> object:
    return fhir_json_response(
        operation_outcome_not_implemented("ValueSet/$expand is not implemented yet."),
        status_code=501,
    )
