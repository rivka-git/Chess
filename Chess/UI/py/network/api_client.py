"""Thin synchronous HTTP client for the API Gateway (history endpoint).

Uses only stdlib urllib so the UI has no extra dependency.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request


class ApiClient:
    def __init__(self, base_url: str) -> None:
        # strip trailing slash for clean joining
        self._base = base_url.rstrip("/")

    def get_history(self, username: str) -> list[dict]:
        url = f"{self._base}/history/{urllib.request.quote(username, safe='')}"
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                return data.get("games", [])
        except urllib.error.URLError:
            return []
