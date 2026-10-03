from dtr_server.infrastructure.fhir.capability_statement_builder import (
    REQUIRED_RESOURCE_OPERATIONS,
    CapabilityStatementBuilder,
)


def _server_rest(capability: dict) -> dict | None:
    for rest in capability.get("rest", []):
        if rest.get("mode") == "server":
            return rest
    return None


def _declared_operations(capability: dict, resource_type: str) -> list[str]:
    rest = _server_rest(capability)
    if rest is None:
        return []
    for entry in rest.get("resource", []):
        if entry.get("type") == resource_type:
            return [op["name"] for op in entry.get("operation", [])]
    return []


def _inferno_operation_errors(capability: dict) -> list[str]:
    errors: list[str] = []
    rest = _server_rest(capability)
    if rest is None:
        errors.append(
            "CapabilityStatement is missing a `rest` entry with `mode` set to `server`."
        )
        return errors

    for resource_type, required_operations in REQUIRED_RESOURCE_OPERATIONS.items():
        operations = _declared_operations(capability, resource_type)
        if not operations and resource_type not in {
            e.get("type") for e in rest.get("resource", [])
        }:
            errors.append(
                f"CapabilityStatement is missing a `{resource_type}` resource entry "
                "in its server-mode `rest` section."
            )
            continue
        if not operations and resource_type not in [
            e.get("type") for e in rest.get("resource", [])
        ]:
            errors.append(
                f"CapabilityStatement is missing a `{resource_type}` resource entry "
                "in its server-mode `rest` section."
            )
            continue

        entry = next(
            (e for e in rest.get("resource", []) if e.get("type") == resource_type),
            None,
        )
        if entry is None:
            errors.append(
                f"CapabilityStatement is missing a `{resource_type}` resource entry "
                "in its server-mode `rest` section."
            )
            continue

        declared = {op["name"] for op in entry.get("operation", [])}
        missing = [op for op in required_operations if op not in declared]
        if missing:
            errors.append(
                f"CapabilityStatement is missing required `{resource_type}` operations: "
                f"{', '.join(f'${name}' for name in missing)}."
            )
    return errors


def test_build_instance_declares_all_required_operations() -> None:
    builder = CapabilityStatementBuilder()
    capability = builder.build_instance("http://example.com/fhir")

    assert capability["resourceType"] == "CapabilityStatement"
    assert capability["kind"] == "instance"
    assert capability["implementation"]["url"] == "http://example.com/fhir"
    assert "http://hl7.org/fhir/us/davinci-dtr/CapabilityStatement/dtr-payer-service" in (
        capability.get("instantiates") or []
    )
    assert _inferno_operation_errors(capability) == []


def test_each_required_operation_is_present() -> None:
    builder = CapabilityStatementBuilder()
    capability = builder.build_instance("http://localhost:8000/fhir")
    rest = _server_rest(capability)
    assert rest is not None

    for resource_type, required_operations in REQUIRED_RESOURCE_OPERATIONS.items():
        declared = _declared_operations(capability, resource_type)
        for operation in required_operations:
            assert operation in declared


def test_inferno_detects_missing_server_rest() -> None:
    capability = {"resourceType": "CapabilityStatement", "rest": []}
    errors = _inferno_operation_errors(capability)
    assert any("mode` set to `server`" in message for message in errors)


def test_inferno_detects_missing_questionnaire_resource() -> None:
    capability = {
        "resourceType": "CapabilityStatement",
        "rest": [{"mode": "server", "resource": [{"type": "ValueSet", "operation": [{"name": "expand"}]}]}],
    }
    errors = _inferno_operation_errors(capability)
    assert any("missing a `Questionnaire` resource entry" in message for message in errors)


def test_inferno_detects_missing_valueset_resource() -> None:
    capability = {
        "resourceType": "CapabilityStatement",
        "rest": [
            {
                "mode": "server",
                "resource": [
                    {
                        "type": "Questionnaire",
                        "operation": [
                            {"name": "questionnaire-package"},
                            {"name": "next-question"},
                            {"name": "log-questionnaire-errors"},
                        ],
                    }
                ],
            }
        ],
    }
    errors = _inferno_operation_errors(capability)
    assert any("missing a `ValueSet` resource entry" in message for message in errors)


def test_inferno_detects_each_missing_operation() -> None:
    for resource_type, required_operations in REQUIRED_RESOURCE_OPERATIONS.items():
        for missing_op in required_operations:
            questionnaire_ops = [
                {"name": "questionnaire-package"},
                {"name": "next-question"},
                {"name": "log-questionnaire-errors"},
            ]
            valueset_ops = [{"name": "expand"}]
            if resource_type == "Questionnaire":
                questionnaire_ops = [op for op in questionnaire_ops if op["name"] != missing_op]
            else:
                valueset_ops = [op for op in valueset_ops if op["name"] != missing_op]

            capability = {
                "resourceType": "CapabilityStatement",
                "rest": [
                    {
                        "mode": "server",
                        "resource": [
                            {"type": "Questionnaire", "operation": questionnaire_ops},
                            {"type": "ValueSet", "operation": valueset_ops},
                        ],
                    }
                ],
            }
            errors = _inferno_operation_errors(capability)
            assert any(f"missing required `{resource_type}` operations: ${missing_op}" in message for message in errors)
