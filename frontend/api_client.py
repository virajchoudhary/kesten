"""Authenticate only requests to the explicitly configured loopback research API."""

import os
from urllib.parse import urlsplit

import requests as http


class ResearchClient:
    exceptions = http.exceptions
    Timeout = http.Timeout

    @property
    def api_url(self):
        url = os.environ.get("CADRISYN_LEGACY_API_URL", "http://127.0.0.1:8001/api").rstrip("/")
        parsed = urlsplit(url)
        if parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("The legacy research client must use an explicit loopback HTTP API.")
        return url

    def request(self, method, url, **kwargs):
        target = urlsplit(url)
        trusted = urlsplit(self.api_url)
        if (target.scheme, target.netloc) == (trusted.scheme, trusted.netloc) and (target.path == trusted.path or target.path.startswith(trusted.path + "/")):
            username = os.environ.get("CADRISYN_LEGACY_USERNAME")
            password = os.environ.get("CADRISYN_LEGACY_PASSWORD")
            if username and password:
                kwargs.setdefault("auth", (username, password))
                kwargs["headers"] = {**(kwargs.get("headers") or {}), "X-Cadrisyn-Research": "1"}
        kwargs.setdefault("timeout", 30)
        return http.request(method, url, **kwargs)

    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)


client = ResearchClient()
