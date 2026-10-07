import os
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx

BACKPORT_NOTIFICATION_PROFILE = (
    "http://hl7.org/fhir/uv/subscriptions-backport/StructureDefinition/backport-subscription-notification-r4"
)
BACKPORT_STATUS_PROFILE = (
    "http://hl7.org/fhir/uv/subscriptions-backport/StructureDefinition/backport-subscription-status-r4"
)


def extract_bearer_token(subscription: dict[str, Any]) -> str:
    for header in subscription.get("channel", {}).get("header") or []:
        if not isinstance(header, str):
            continue
        if header.lower().startswith("authorization:") and "bearer " in header.lower():
            return header.split("Bearer ", 1)[-1].strip()
    return os.getenv("INFERNO_NOTIFICATION_TOKEN", "default-fallback-token")


def content_type_for_subscription(subscription: dict[str, Any]) -> str:
    payload = subscription.get("channel", {}).get("payload")
    if payload in ("application/fhir+json", "application/json"):
        return payload
    return "application/fhir+json"


def build_handshake_bundle(
    subscription: dict[str, Any],
    fhir_base_url: str,
    subscription_id: str,
) -> dict[str, Any]:
    topic = subscription.get("criteria", "")
    subscription_url = f"{fhir_base_url.rstrip('/')}/Subscription/{subscription_id}"
    status_url = f"{subscription_url}/$status"
    param_id = str(uuid.uuid4())
    entry_full_url = f"urn:uuid:{param_id}"

    return {
        "resourceType": "Bundle",
        "type": "history",
        "timestamp": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "meta": {"profile": [BACKPORT_NOTIFICATION_PROFILE]},
        "entry": [
            {
                "fullUrl": entry_full_url,
                "resource": {
                    "resourceType": "Parameters",
                    "id": param_id,
                    "meta": {"profile": [BACKPORT_STATUS_PROFILE]},
                    "parameter": [
                        {"name": "subscription", "valueReference": {"reference": subscription_url}},
                        {"name": "topic", "valueCanonical": topic},
                        {"name": "status", "valueCode": "requested"},
                        {"name": "type", "valueCode": "handshake"},
                        {"name": "events-since-subscription-start", "valueString": "0"},
                    ],
                },
                "request": {"method": "GET", "url": status_url},
                "response": {"status": "200"},
            }
        ],
    }


async def send_handshake_notification(
    subscription: dict[str, Any],
    subscription_id: str,
    fhir_base_url: str,
) -> bool:
    endpoint = subscription.get("channel", {}).get("endpoint")
    if not endpoint:
        return False

    bundle = build_handshake_bundle(subscription, fhir_base_url, subscription_id)
    token = extract_bearer_token(subscription)
    content_type = content_type_for_subscription(subscription)
    headers = {
        "Content-Type": content_type,
        "Authorization": f"Bearer {token}",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint, json=bundle, headers=headers)
        return 200 <= response.status_code < 300
    except httpx.HTTPError:
        return False
