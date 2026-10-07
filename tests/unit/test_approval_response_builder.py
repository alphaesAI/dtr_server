import json
from pathlib import Path

from src.api.infrastructure.approval_response_builder import ApprovalResponseBundleBuilder
from src.api.infrastructure.pas_profiles import (
    PROFILE_CLAIM_RESPONSE,
    PROFILE_RESPONSE_BUNDLE,
    REVIEW_ACTION_APPROVED,
)
from src.api.infrastructure.pas_request_parser import PasRequestBundleParser

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "pas_request_bundle_minimal.json"


def _parsed_request():
    bundle = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return PasRequestBundleParser().parse(bundle)


def claim_response_item_extensions(bundle: dict) -> list:
    return bundle["entry"][0]["resource"]["item"][0].get("extension") or []


def test_approval_response_shape_and_a1_decision() -> None:
    request = _parsed_request()
    bundle = ApprovalResponseBundleBuilder("https://example.org/fhir").build(request)

    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "collection"
    assert PROFILE_RESPONSE_BUNDLE in bundle["meta"]["profile"]
    assert "identifier" in bundle
    assert bundle["identifier"].get("value")
    assert bundle["entry"][0]["resource"]["resourceType"] == "ClaimResponse"

    quantity = None
    for ext in claim_response_item_extensions(bundle):
        if ext.get("url", "").endswith("extension-itemAuthorizedDetail"):
            for nested in ext.get("extension") or []:
                if nested.get("url") == "quantity":
                    quantity = nested["valueQuantity"]
    assert quantity is not None
    assert quantity.get("value") is not None
    assert quantity.get("unit") or quantity.get("code")

    claim_response = bundle["entry"][0]["resource"]
    assert PROFILE_CLAIM_RESPONSE in claim_response["meta"]["profile"]
    assert claim_response["request"]["reference"] == request.claim_full_url
    assert claim_response["outcome"] == "complete"
    assert claim_response["use"] == "preauthorization"

    adjudication = claim_response["item"][0]["adjudication"][0]
    review = adjudication["extension"][0]
    codes = [
        nested
        for nested in review["extension"]
        if nested.get("valueCodeableConcept")
    ]
    assert codes
    coding = codes[0]["valueCodeableConcept"]["coding"][0]
    assert coding["code"] == REVIEW_ACTION_APPROVED


def test_echoed_resources_preserve_exact_full_urls() -> None:
    request = _parsed_request()
    request_full_urls = {
        e.full_url: e.resource.get("resourceType") for e in request.entries
    }
    bundle = ApprovalResponseBundleBuilder("https://example.org/fhir").build(request)

    echoed = bundle["entry"][1:]
    assert echoed, "expected echoed supporting resources"

    for entry in echoed:
        full_url = entry["fullUrl"]
        assert full_url in request_full_urls
        assert entry["resource"]["resourceType"] == request_full_urls[full_url]
        # Exact string match — no rewriting of host or path
        original = next(e for e in request.entries if e.full_url == full_url)
        assert entry["fullUrl"] == original.full_url


def test_patient_full_url_unchanged() -> None:
    request = _parsed_request()
    patient_url = "http://example.org/fhir/Patient/SubscriberExample"
    bundle = ApprovalResponseBundleBuilder("https://example.org/fhir").build(request)
    patient_entries = [
        e for e in bundle["entry"] if e["resource"].get("resourceType") == "Patient"
    ]
    assert len(patient_entries) == 1
    assert patient_entries[0]["fullUrl"] == patient_url
