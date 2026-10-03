from fastapi import FastAPI

from dtr_server import __version__
from dtr_server.presentation.api.auth_router import router as auth_router
from dtr_server.presentation.api.fhir_router import router as fhir_router
from dtr_server.presentation.api.smart_router import router as smart_router

app = FastAPI(
    title="Da Vinci DTR Payer Server",
    version=__version__,
    description="FHIR server implementing DTR Payer Service capabilities.",
)

app.include_router(fhir_router, prefix="/fhir", tags=["fhir"])
app.include_router(smart_router, prefix="/fhir", tags=["smart"])
app.include_router(auth_router, prefix="/fhir/auth", tags=["auth"])


@app.get("/health")
def root_health() -> dict[str, str]:
    return {"status": "ok"}
