"""Seller store settings; backend scope: settings:read."""

from __future__ import annotations

from mcp.server import MCPServer

from ecommerce_mcp.clients.store_client import StoreClient
from ecommerce_mcp.models.schemas import money


def register_settings_tools(mcp: MCPServer) -> None:
    @mcp.tool()
    async def get_store_settings() -> dict:
        """Get store identity, public contact details, and current homepage text."""
        async with StoreClient() as client:
            settings = await client.settings()
        return {
            "name": settings.storeName,
            "tagline": settings.storeTagline,
            "contact_email": settings.email,
            "contact_phone": settings.phone,
            "hero_title": settings.heroTitle,
            "hero_intro": settings.heroIntro,
            "updated_at": settings.updatedAt.isoformat() if settings.updatedAt else None,
        }

    @mcp.tool()
    async def get_shipping_settings() -> dict:
        """Read shipping mode, flat shipping fee, and free-shipping threshold."""
        async with StoreClient() as client:
            settings = await client.settings()
        return {
            "shipping_mode": settings.shippingMode,
            "shipping_fee": money(settings.shippingFee) if settings.shippingFee is not None else None,
            "free_shipping_threshold": money(settings.freeShippingThreshold)
            if settings.freeShippingThreshold is not None else None,
            "currency": "Not specified by the current backend API",
        }
