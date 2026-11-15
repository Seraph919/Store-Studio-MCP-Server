"""Authenticated read-only HTTP client for the Spring Boot MCP endpoints."""

from __future__ import annotations

import httpx
from pydantic import TypeAdapter, ValidationError

from ecommerce_mcp.config import Settings
from ecommerce_mcp.models.schemas import Product, SellerKpis, SellerOrder, StoreSettings


class StoreAPIError(RuntimeError):
    """Readable, credential-safe error surfaced to the MCP caller."""


class StoreClient:
    """One HTTP client per tool invocation (or shared within a multi-fetch tool)."""

    def __init__(
        self,
        settings: Settings | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings or Settings.from_env()
        self._transport = transport
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "StoreClient":
        self._client = httpx.AsyncClient(
            base_url=self.settings.store_api_url,
            timeout=self.settings.timeout_seconds,
            headers={"X-API-Key": self.settings.store_api_key, "Accept": "application/json"},
            transport=self._transport,
            follow_redirects=False,
            trust_env=False,  # Prevent environment proxies receiving long-lived keys.
        )
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _get(self, endpoint: str):
        if self._client is None:
            raise RuntimeError("Use StoreClient inside 'async with'.")
        try:
            response = await self._client.get(f"/api/v1/mcp/{endpoint}")
        except httpx.TimeoutException as exc:
            raise StoreAPIError("Store API timed out. Check that the backend is running.") from exc
        except httpx.RequestError as exc:
            raise StoreAPIError("Store API unreachable. Check STORE_API_URL and backend connectivity.") from exc

        if response.status_code == 401:
            raise StoreAPIError("401 Unauthorized: invalid, expired or revoked STORE_API_KEY.")
        if response.status_code == 403:
            raise StoreAPIError(f"403 Forbidden: API key lacks permission to read {endpoint}.")
        if not response.is_success:
            raise StoreAPIError(f"Store API returned HTTP {response.status_code} while reading {endpoint}.")
        try:
            return response.json()
        except ValueError as exc:
            raise StoreAPIError(f"Store API returned non-JSON data for {endpoint}.") from exc

    async def products(self) -> list[Product]:
        return await self._parsed("products", list[Product])

    async def orders(self) -> list[SellerOrder]:
        return await self._parsed("orders", list[SellerOrder])

    async def analytics(self) -> SellerKpis:
        return await self._parsed("analytics", SellerKpis)

    async def settings(self) -> StoreSettings:
        return await self._parsed("settings", StoreSettings)

    async def _parsed(self, endpoint: str, model_type):
        try:
            return TypeAdapter(model_type).validate_python(await self._get(endpoint))
        except ValidationError as exc:
            raise StoreAPIError(f"Unexpected {endpoint} response structure from store backend.") from exc
