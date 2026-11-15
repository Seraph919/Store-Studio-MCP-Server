"""Environment configuration for the seller's store API."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import urlparse

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    store_api_url: str
    store_api_key: str
    timeout_seconds: float = 15.0
    allow_insecure_http: bool = False

    @classmethod
    def from_env(cls) -> "Settings":
        # Searches parent directories for .env; works when server.py is run directly.
        load_dotenv()
        url = os.getenv("STORE_API_URL", "http://localhost:8080").strip().rstrip("/")
        key = os.getenv("STORE_API_KEY", "").strip()
        if not key:
            raise ValueError("STORE_API_KEY is missing. Generate a key in Seller > API Keys.")
        if not url:
            raise ValueError("STORE_API_URL must not be empty.")

        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("STORE_API_URL must be an absolute http(s) URL.")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError("STORE_API_URL must not contain credentials, query parameters or a fragment.")
        if parsed.path not in {"", "/"}:
            raise ValueError("STORE_API_URL must be the origin only, e.g. http://localhost:8080.")

        allow_http = os.getenv("STORE_ALLOW_INSECURE_HTTP", "false").lower() in {"true", "1", "yes"}
        if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"} and not allow_http:
            raise ValueError(
                "Refusing to send an API key over unencrypted HTTP. Use HTTPS or set "
                "STORE_ALLOW_INSECURE_HTTP=true for an isolated trusted Docker network."
            )
        timeout = float(os.getenv("STORE_TIMEOUT_SECONDS", "15"))
        if not (0 < timeout <= 120):
            raise ValueError("STORE_TIMEOUT_SECONDS must be between 0 and 120.")

        return cls(store_api_url=url, store_api_key=key, timeout_seconds=timeout, allow_insecure_http=allow_http)
