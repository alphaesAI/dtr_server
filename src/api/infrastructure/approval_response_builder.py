import uuid
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from src.api.domain.pas_submit import BundleEntry, PasSubmitRequest
from src.api.infrastructure import pas_profiles as profiles


class ApprovalResponseBundleBuilder:
    """Build a PAS Response Bundle with Approval (A1) for every Claim item."""

    def __init__(self, fhir_base_url: str) -> None:
        self._fhir_base = fhir_base_url.rstrip("/")

    def build(self, request: PasSubmitRequest) -> dict[str, Any]:
        claim = request.claim
        claim_id = claim.get("id") or "unknown"
        response_id = str(uuid.uuid4())
        now = datetime.now(UTC)
        created = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        today = now.strftime("%Y-%m-%d")

        claim_response = self._build_claim_response(
            claim=claim,
            claim_id=claim_id,
            claim_full_url=request.claim_full_url,
            response_id=response_id,
            created=created,
            today=today,
            request=request,
        )

        claim_response_full_url = f"{self._fhir_base}/ClaimResponse/{response_id}"
        entries: list[dict[str, Any]] = [
            {"fullUrl": claim_response_full_url, "resource": claim_response}
        ]

        for echoed in self._echoed_entries_for_claim_response(claim_response, request):
            entries.append(
                {
                    "fullUrl": echoed.full_url,
                    "resource": deepcopy(echoed.resource),
                }
            )

        response_bundle: dict[str, Any] = {
            "resourceType": "Bundle",
            "id": str(uuid.uuid4()),
            "meta": {"profile": [profiles.PROFILE_RESPONSE_BUNDLE]},
            "identifier": self._bundle_identifier(request),
            "type": "collection",
            "timestamp": created,
            "entry": entries,
        }
        return response_bundle

    def _bundle_identifier(self, request: PasSubmitRequest) -> dict[str, Any]:
        """PAS Response Bundle requires identifier (1..1); echo request or synthesize."""
        if request.bundle_identifier:
            return deepcopy(request.bundle_identifier)
        return {
            "system": "urn:ietf:rfc:3986",
            "value": f"urn:uuid:{uuid.uuid4()}",
        }

    def _build_claim_response(
        self,
        *,
        claim: dict[str, Any],
        claim_id: str,
        claim_full_url: str,
        response_id: str,
        created: str,
        today: str,
        request: PasSubmitRequest,
    ) -> dict[str, Any]:
        claim_response: dict[str, Any] = {
            "resourceType": "ClaimResponse",
            "id": response_id,
            "meta": {"profile": [profiles.PROFILE_CLAIM_RESPONSE]},
            "status": claim.get("status") or "active",
            "type": deepcopy(claim.get("type") or {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/claim-type",
                        "code": "professional",
                    }
                ]
            }),
            "use": "preauthorization",
            "patient": deepcopy(claim.get("patient") or {}),
            "created": created,
            "insurer": deepcopy(claim.get("insurer") or {}),
            "requestor": deepcopy(claim.get("provider") or claim.get("requestor") or {}),
            "request": {"reference": claim_full_url or f"Claim/{claim_id}"},
            "outcome": "complete",
            "item": [],
        }

        if claim.get("identifier"):
            claim_response["identifier"] = deepcopy(claim["identifier"])

        provider_ref = self._authorized_provider_ref(claim, request)

        for item in claim.get("item") or []:
            if not isinstance(item, dict):
                continue
            sequence = item.get("sequence")
            if sequence is None:
                continue
            claim_response["item"].append(
                self._build_item_response(
                    item, sequence=sequence, today=today, provider_ref=provider_ref
                )
            )

        if not claim_response["item"]:
            claim_response["item"].append(
                self._build_item_response(
                    {"sequence": 1}, sequence=1, today=today, provider_ref=provider_ref
                )
            )

        return claim_response

    def _build_item_response(
        self,
        claim_item: dict[str, Any],
        *,
        sequence: int,
        today: str,
        provider_ref: dict[str, Any] | None,
    ) -> dict[str, Any]:
        period = self._service_period(claim_item, today)
        extensions: list[dict[str, Any]] = [
            {
                "url": profiles.EXT_ITEM_REQUESTED_SERVICE_DATE,
                "valuePeriod": deepcopy(period),
            },
            {
                "url": profiles.EXT_ITEM_PREAUTH_ISSUE_DATE,
                "valueDate": today,
            },
            {
                "url": profiles.EXT_ITEM_PREAUTH_PERIOD,
                "valuePeriod": deepcopy(period),
            },
        ]

        if provider_ref:
            extensions.append(
                {
                    "url": profiles.EXT_ITEM_AUTHORIZED_PROVIDER,
                    "extension": [
                        {"url": "provider", "valueReference": deepcopy(provider_ref)}
                    ],
                }
            )

        product = claim_item.get("productOrService") or claim_item.get("category")
        if product:
            detail_ext: list[dict[str, Any]] = [
                {"url": "productOrServiceCode", "valueCodeableConcept": deepcopy(product)}
            ]
            if claim_item.get("unitPrice"):
                detail_ext.append(
                    {"url": "unitPrice", "valueMoney": deepcopy(claim_item["unitPrice"])}
                )
            quantity = self._authorized_quantity(claim_item)
            detail_ext.append({"url": "quantity", "valueQuantity": quantity})
            extensions.append(
                {"url": profiles.EXT_ITEM_AUTHORIZED_DETAIL, "extension": detail_ext}
            )

        auth_number = f"AUTH{sequence:04d}"
        return {
            "extension": extensions,
            "itemSequence": sequence,
            "adjudication": [
                {
                    "extension": [
                        {
                            "url": profiles.EXT_REVIEW_ACTION,
                            "extension": [
                                {"url": "number", "valueString": auth_number},
                                {
                                    "url": profiles.EXT_REVIEW_ACTION_CODE,
                                    "valueCodeableConcept": {
                                        "coding": [
                                            {
                                                "system": profiles.X12_REVIEW_ACTION_SYSTEM,
                                                "code": profiles.REVIEW_ACTION_APPROVED,
                                                "display": profiles.REVIEW_ACTION_APPROVED_DISPLAY,
                                            }
                                        ]
                                    },
                                },
                            ],
                        }
                    ],
                    "category": {
                        "coding": [
                            {
                                "system": profiles.ADJUDICATION_CATEGORY_SYSTEM,
                                "code": profiles.ADJUDICATION_SUBMITTED,
                            }
                        ]
                    },
                }
            ],
        }

    def _authorized_quantity(self, claim_item: dict[str, Any]) -> dict[str, Any]:
        """Quantity must satisfy prof-2: value plus unit and/or code."""
        default = {
            "value": 1,
            "unit": "visit",
            "system": "http://unitsofmeasure.org",
            "code": "1",
        }
        quantity = claim_item.get("quantity")
        if quantity is None:
            return default
        if not isinstance(quantity, dict):
            return {**default, "value": quantity}
        result = deepcopy(quantity)
        if "value" not in result:
            result["value"] = 1
        if not result.get("unit") and not result.get("code"):
            result["unit"] = default["unit"]
            result["system"] = default["system"]
            result["code"] = default["code"]
        return result

    def _service_period(self, claim_item: dict[str, Any], today: str) -> dict[str, str]:
        if isinstance(claim_item.get("servicedPeriod"), dict):
            period = claim_item["servicedPeriod"]
            return {
                "start": period.get("start") or today,
                "end": period.get("end") or period.get("start") or today,
            }
        if claim_item.get("servicedDate"):
            date = claim_item["servicedDate"]
            return {"start": date, "end": date}
        return {"start": today, "end": today}

    def _authorized_provider_ref(
        self, claim: dict[str, Any], request: PasSubmitRequest
    ) -> dict[str, Any] | None:
        for team in claim.get("careTeam") or []:
            if not isinstance(team, dict):
                continue
            provider = team.get("provider")
            if not isinstance(provider, dict) or not provider.get("reference"):
                continue
            reference = provider["reference"]
            entry = request.entry_by_reference(reference)
            if entry and entry.resource.get("resourceType") == "PractitionerRole":
                practitioner = entry.resource.get("practitioner")
                if isinstance(practitioner, dict) and practitioner.get("reference"):
                    return {"reference": practitioner["reference"]}
            return {"reference": reference}
        return None

    def _echoed_entries_for_claim_response(
        self,
        claim_response: dict[str, Any],
        request: PasSubmitRequest,
    ) -> list[BundleEntry]:
        """Copy request entries for every reference on ClaimResponse, preserving exact fullUrl."""
        references = self._collect_references(claim_response)
        seen_full_urls: set[str] = set()
        echoed: list[BundleEntry] = []

        for reference in references:
            entry = request.entry_by_reference(reference)
            if entry is None:
                continue
            if entry.full_url in seen_full_urls:
                continue
            # Never echo the Claim itself as a response entry (ClaimResponse.request is enough).
            if entry.resource.get("resourceType") == "Claim":
                continue
            seen_full_urls.add(entry.full_url)
            echoed.append(entry)

        return echoed

    def _collect_references(self, resource: Any) -> list[str]:
        refs: list[str] = []

        def walk(node: Any) -> None:
            if isinstance(node, dict):
                if "reference" in node and isinstance(node["reference"], str):
                    refs.append(node["reference"])
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(resource)
        return refs
