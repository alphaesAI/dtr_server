from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from dtr_server.application.build_smart_configuration import BuildSmartConfiguration
from dtr_server.presentation.api.dependencies import get_smart_configuration_builder

router = APIRouter()


@router.get("/.well-known/smart-configuration")
def smart_configuration(
    builder: BuildSmartConfiguration = Depends(get_smart_configuration_builder),
) -> JSONResponse:
    return JSONResponse(content=builder.execute(), media_type="application/json")
