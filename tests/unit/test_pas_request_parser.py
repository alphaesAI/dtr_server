import pytest

from src.api.domain.errors import InvalidPasRequestError
from src.api.infrastructure.pas_request_parser import PasRequestBundleParser


def test_parse_extracts_single_claim_and_preserves_full_urls() -> None:
    bundle = {
        "resourceType": "Bundle",
        "entry": [
            {
                "fullUrl": "http://example.org/fhir/Claim/c1",
                "resource": {"resourceType": "Claim", "id": "c1"},
            },
            {
                "fullUrl": "http://example.org/fhir/Patient/p1",
                "resource": {"resourceType": "Patient", "id": "p1"},
            },
        ],
    }
    parsed = PasRequestBundleParser().parse(bundle)
    assert parsed.claim["id"] == "c1"
    assert parsed.claim_full_url == "http://example.org/fhir/Claim/c1"
    assert len(parsed.entries) == 2
    assert parsed.entries[1].full_url == "http://example.org/fhir/Patient/p1"


def test_parse_rejects_missing_claim() -> None:
    bundle = {
        "resourceType": "Bundle",
        "entry": [
            {
                "fullUrl": "http://example.org/fhir/Patient/p1",
                "resource": {"resourceType": "Patient", "id": "p1"},
            }
        ],
    }
    with pytest.raises(InvalidPasRequestError, match="exactly one Claim"):
        PasRequestBundleParser().parse(bundle)


def test_parse_rejects_multiple_claims() -> None:
    bundle = {
        "resourceType": "Bundle",
        "entry": [
            {
                "fullUrl": "http://example.org/fhir/Claim/c1",
                "resource": {"resourceType": "Claim", "id": "c1"},
            },
            {
                "fullUrl": "http://example.org/fhir/Claim/c2",
                "resource": {"resourceType": "Claim", "id": "c2"},
            },
        ],
    }
    with pytest.raises(InvalidPasRequestError, match="exactly one Claim"):
        PasRequestBundleParser().parse(bundle)


def test_parse_rejects_entry_without_full_url() -> None:
    bundle = {
        "resourceType": "Bundle",
        "entry": [{"resource": {"resourceType": "Claim", "id": "c1"}}],
    }
    with pytest.raises(InvalidPasRequestError, match="fullUrl"):
        PasRequestBundleParser().parse(bundle)
