import json

from fastapi import APIRouter, Depends, Form, Response

from dtr_server.application.exchange_backend_services_token import (
    ExchangeBackendServicesToken,
    OAuthError,
    TokenRequest,
)
from dtr_server.presentation.api.dependencies import get_token_exchange_use_case

router = APIRouter()


@router.post("/token")
def backend_services_token(
    grant_type: str | None = Form(default=None),
    client_assertion_type: str | None = Form(default=None),
    client_assertion: str | None = Form(default=None),
    scope: str | None = Form(default=None),
    use_case: ExchangeBackendServicesToken = Depends(get_token_exchange_use_case),
) -> Response:
    try:
        body = use_case.execute(
            TokenRequest(
                grant_type=grant_type,
                client_assertion_type=client_assertion_type,
                client_assertion=client_assertion,
                scope=scope,
            )
        )
    except OAuthError as exc:
        return Response(
            content=json.dumps({"error": exc.error, "error_description": exc.description}),
            status_code=exc.status_code,
            media_type="application/json",
        )

    return Response(
        content=json.dumps(body),
        status_code=200,
        media_type="application/json",
        headers={"Cache-Control": "no-store", "Pragma": "no-cache"},
    )


@router.get("/authorize")
def authorize_not_implemented() -> Response:
    return Response(
        content='{"error":"not_supported","error_description":"Authorization code flow is not implemented."}',
        status_code=501,
        media_type="application/json",
    )
