import json
import time
from typing import Any

import httpx

from dtr_server.config import Settings


def merge_jwks(*documents: dict[str, Any]) -> dict[str, Any]:
    merged: list[dict[str, Any]] = []
    seen_kids: set[str] = set()

    for document in documents:
        for key in document.get("keys") or []:
            if "d" in key:
                continue
            kid = key.get("kid")
            if kid and kid in seen_kids:
                continue
            if kid:
                seen_kids.add(kid)
            merged.append(key)

    return {"keys": merged}


class JwksResolver:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._cache: dict[str, Any] | None = None
        self._cache_expires_at: float = 0.0

    def resolve(self) -> dict[str, Any]:
        now = time.time()
        if self._cache is not None and now < self._cache_expires_at:
            return self._cache

        documents = [self._settings.load_trusted_jwks()]
        for url in self._settings.smart_jwks_url_list:
            documents.append(self._fetch_jwks(url))

        merged = merge_jwks(*documents)
        self._cache = merged
        self._cache_expires_at = now + self._settings.smart_jwks_cache_seconds
        return merged

    def _fetch_jwks(self, url: str) -> dict[str, Any]:
        try:
            response = httpx.get(url, timeout=10.0, follow_redirects=True)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            if not self._settings.smart_jwks_fetch_optional:
                raise RuntimeError(f"Failed to fetch JWKS from {url}: {exc}") from exc
            return {"keys": []}

        if not isinstance(payload, dict) or "keys" not in payload:
            return {"keys": []}
        return payload
