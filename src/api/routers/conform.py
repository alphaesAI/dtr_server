import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter
from fastapi.responses import Response

load_dotenv()

router = APIRouter(tags=["Discovery"])

_PAS_CAPABILITY_PATH = (
    Path(__file__).resolve().parent.parent.parent / "fhir" / "pas" / "capabilitystatement.json"
)


@router.get("/metadata")
async def get_capability_statement() -> Response:
    """Serves the PAS CapabilityStatement for Inferno Discovery / Subscription Setup."""
    if not _PAS_CAPABILITY_PATH.is_file():
        body = {
            "resourceType": "CapabilityStatement",
            "status": "error",
            "message": "CapabilityStatement file not found",
        }
        return Response(content=json.dumps(body), media_type="application/fhir+json", status_code=500)

    document = json.loads(_PAS_CAPABILITY_PATH.read_text(encoding="utf-8"))
    fhir_base = os.getenv("PUBLIC_FHIR_BASE_URL", "http://localhost:8000/fhir").rstrip("/")
    document["implementation"] = {
        "description": "PAS Payer Server FHIR endpoint",
        "url": fhir_base,
    }
    return Response(
        content=json.dumps(document),
        media_type="application/fhir+json",
        status_code=200,
    )
