from typing import Any


def operation_outcome_not_implemented(detail: str) -> dict[str, Any]:
    return {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "error",
                "code": "not-supported",
                "diagnostics": detail,
            }
        ],
    }
