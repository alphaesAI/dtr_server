import os
import uuid
from typing import Any, Dict

from dotenv import load_dotenv
from fastapi import APIRouter, BackgroundTasks, Response, status

from src.api.services.subscription_handshake import send_handshake_notification

load_dotenv()

NOTIFICATION_TOKEN = os.getenv("INFERNO_NOTIFICATION_TOKEN", "default-fallback-token")
PUBLIC_FHIR_BASE_URL = os.getenv("PUBLIC_FHIR_BASE_URL", "http://localhost:8000/fhir").rstrip("/")

router = APIRouter(tags=["Subscription"])

ACTIVE_SUBSCRIPTIONS: Dict[str, Dict[str, Any]] = {}


async def _complete_subscription_handshake(subscription: dict[str, Any], subscription_id: str) -> None:
    accepted = await send_handshake_notification(subscription, subscription_id, PUBLIC_FHIR_BASE_URL)
    if accepted and subscription_id in ACTIVE_SUBSCRIPTIONS:
        ACTIVE_SUBSCRIPTIONS[subscription_id]["status"] = "active"


@router.post("/Subscription", status_code=status.HTTP_201_CREATED)
async def create_subscription(
    payload: Dict[str, Any],
    response: Response,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """Create Subscription (requested), send rest-hook handshake, then set active if accepted."""
    sub_id = payload.get("id") or str(uuid.uuid4())
    payload["id"] = sub_id
    payload["status"] = "requested"

    ACTIVE_SUBSCRIPTIONS[sub_id] = payload

    response.headers["Location"] = f"{PUBLIC_FHIR_BASE_URL}/Subscription/{sub_id}"
    background_tasks.add_task(_complete_subscription_handshake, dict(payload), sub_id)
    return payload
