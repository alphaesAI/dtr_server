import copy
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from dtr_server import __version__

DTR_PAYER_SERVICE_CANONICAL = (
    "http://hl7.org/fhir/us/davinci-dtr/CapabilityStatement/dtr-payer-service"
)
OFFICIAL_CS_PATH = (
    Path(__file__).resolve().parent / "official" / "CapabilityStatement-dtr-payer-service.json"
)

REQUIRED_RESOURCE_OPERATIONS: dict[str, list[str]] = {
    "Questionnaire": [
        "questionnaire-package",
        "next-question",
        "log-questionnaire-errors",
    ],
    "ValueSet": ["expand"],
}


class CapabilityStatementBuilder:
    def build_instance(self, fhir_base_url: str) -> dict[str, Any]:
        requirements = self._load_official_requirements()
        rest_block = copy.deepcopy(requirements["rest"])

        return {
            "resourceType": "CapabilityStatement",
            "status": "active",
            "date": datetime.now(UTC).strftime("%Y-%m-%d"),
            "publisher": requirements.get("publisher"),
            "description": requirements.get("description"),
            "kind": "instance",
            "software": {
                "name": "dtr-server",
                "version": __version__,
            },
            "implementation": {
                "description": "Da Vinci DTR Payer Server",
                "url": fhir_base_url.rstrip("/"),
            },
            "instantiates": [DTR_PAYER_SERVICE_CANONICAL],
            "fhirVersion": requirements.get("fhirVersion", "4.0.1"),
            "format": requirements.get("format", ["json"]),
            "rest": rest_block,
        }

    def _load_official_requirements(self) -> dict[str, Any]:
        with OFFICIAL_CS_PATH.open(encoding="utf-8") as handle:
            return json.load(handle)
