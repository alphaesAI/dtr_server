from copy import deepcopy
from typing import Any

from src.api.domain.errors import InvalidPasRequestError
from src.api.domain.pas_submit import BundleEntry, PasSubmitRequest


class PasRequestBundleParser:
    """Extract exactly one Claim and preserve every entry fullUrl from a PAS Request Bundle."""

    def parse(self, bundle: dict[str, Any]) -> PasSubmitRequest:
        if not isinstance(bundle, dict) or bundle.get("resourceType") != "Bundle":
            raise InvalidPasRequestError("Request body must be a FHIR Bundle.")

        entries_raw = bundle.get("entry") or []
        if not isinstance(entries_raw, list) or not entries_raw:
            raise InvalidPasRequestError("Bundle.entry must contain at least one entry.")

        entries: list[BundleEntry] = []
        claim_entries: list[BundleEntry] = []

        for index, raw in enumerate(entries_raw):
            if not isinstance(raw, dict):
                raise InvalidPasRequestError(f"Bundle.entry[{index}] must be an object.")
            resource = raw.get("resource")
            if not isinstance(resource, dict) or not resource.get("resourceType"):
                raise InvalidPasRequestError(
                    f"Bundle.entry[{index}] must include a resource with resourceType."
                )
            full_url = raw.get("fullUrl")
            if not isinstance(full_url, str) or not full_url:
                raise InvalidPasRequestError(
                    f"Bundle.entry[{index}] must include a non-empty fullUrl."
                )
            entry = BundleEntry(full_url=full_url, resource=deepcopy(resource))
            entries.append(entry)
            if resource.get("resourceType") == "Claim":
                claim_entries.append(entry)

        if len(claim_entries) != 1:
            raise InvalidPasRequestError(
                f"PAS Request Bundle must contain exactly one Claim; found {len(claim_entries)}."
            )

        claim_entry = claim_entries[0]
        identifier = bundle.get("identifier")
        if identifier is not None and not isinstance(identifier, dict):
            raise InvalidPasRequestError("Bundle.identifier must be an Identifier object.")
        return PasSubmitRequest(
            claim=claim_entry.resource,
            claim_full_url=claim_entry.full_url,
            entries=entries,
            bundle_identifier=deepcopy(identifier) if isinstance(identifier, dict) else None,
            bundle_id=bundle.get("id") if isinstance(bundle.get("id"), str) else None,
        )
