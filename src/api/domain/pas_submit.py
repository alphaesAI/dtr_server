from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BundleEntry:
    """One Bundle.entry, preserving the exact fullUrl from the request."""

    full_url: str
    resource: dict[str, Any]


@dataclass
class PasSubmitRequest:
    """Parsed PAS Request Bundle ready for adjudication."""

    claim: dict[str, Any]
    claim_full_url: str
    entries: list[BundleEntry] = field(default_factory=list)
    bundle_identifier: dict[str, Any] | None = None
    bundle_id: str | None = None

    def entry_by_reference(self, reference: str) -> BundleEntry | None:
        """Resolve a FHIR reference against request entries (relative or absolute)."""
        if not reference:
            return None
        for entry in self.entries:
            resource = entry.resource
            resource_type = resource.get("resourceType", "")
            resource_id = resource.get("id", "")
            relative = f"{resource_type}/{resource_id}" if resource_id else ""
            if reference == entry.full_url or reference == relative:
                return entry
            if relative and reference.endswith(f"/{relative}"):
                return entry
        return None
