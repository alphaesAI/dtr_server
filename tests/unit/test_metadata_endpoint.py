from fastapi.testclient import TestClient

from dtr_server.infrastructure.fhir.capability_statement_builder import REQUIRED_RESOURCE_OPERATIONS
from dtr_server.main import app

client = TestClient(app)


def test_metadata_returns_fhir_capability_statement() -> None:
    response = client.get("/fhir/metadata")

    assert response.status_code == 200
    assert "application/fhir+json" in response.headers["content-type"]

    capability = response.json()
    assert capability["resourceType"] == "CapabilityStatement"
    assert capability["kind"] == "instance"

    server_rest = next(r for r in capability["rest"] if r["mode"] == "server")
    for resource_type, operations in REQUIRED_RESOURCE_OPERATIONS.items():
        entry = next(e for e in server_rest["resource"] if e["type"] == resource_type)
        declared = {op["name"] for op in entry.get("operation", [])}
        for operation in operations:
            assert operation in declared


def test_stub_operations_return_501() -> None:
    stubs = [
        "/fhir/Questionnaire/$questionnaire-package",
        "/fhir/Questionnaire/$next-question",
        "/fhir/Questionnaire/$log-questionnaire-errors",
        "/fhir/ValueSet/$expand",
    ]
    for path in stubs:
        response = client.post(path)
        assert response.status_code == 501
        assert response.json()["resourceType"] == "OperationOutcome"
