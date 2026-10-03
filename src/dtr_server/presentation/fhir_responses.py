from typing import Any

from fastapi.responses import JSONResponse


def fhir_json_response(resource: dict[str, Any], status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        content=resource,
        status_code=status_code,
        media_type="application/fhir+json; charset=utf-8",
    )
