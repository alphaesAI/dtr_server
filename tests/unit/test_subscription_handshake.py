from src.api.services.subscription_handshake import build_handshake_bundle, extract_bearer_token


def test_build_handshake_bundle_shape() -> None:
    subscription = {
        "criteria": "http://hl7.org/fhir/us/davinci-pas/SubscriptionTopic/PASSubscriptionTopic",
        "channel": {
            "type": "rest-hook",
            "endpoint": "https://example.org/notify",
            "header": ["Authorization: Bearer test-token-123"],
            "payload": "application/fhir+json",
        },
    }
    bundle = build_handshake_bundle(subscription, "https://example.org/fhir", "sub-42")

    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "history"
    entry = bundle["entry"][0]
    assert entry["request"]["url"].endswith("Subscription/sub-42/$status")
    params = entry["resource"]["parameter"]
    types = {p["name"]: p for p in params}
    assert types["type"]["valueCode"] == "handshake"
    assert types["status"]["valueCode"] == "requested"
    assert types["events-since-subscription-start"]["valueString"] == "0"


def test_extract_bearer_from_channel_header() -> None:
    sub = {"channel": {"header": ["Authorization: Bearer abc"]}}
    assert extract_bearer_token(sub) == "abc"
