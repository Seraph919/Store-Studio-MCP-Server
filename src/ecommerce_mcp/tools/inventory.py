"""Inventory checks derived from the seller's product endpoint."""

from __future__ import annotations

from mcp.server import MCPServer

from ecommerce_mcp.clients.store_client import StoreClient
from ecommerce_mcp.models.schemas import product_summary


def register_inventory_tools(mcp: MCPServer) -> None:
    @mcp.tool()
    async def get_low_stock_products(threshold: int = 3, limit: int = 50) -> dict:
        """List products at or below a stock threshold, including out-of-stock items."""
        if threshold < 0:
            raise ValueError("threshold cannot be negative")
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        async with StoreClient() as client:
            products = await client.products()
        low = [p for p in products if p.quantity is not None and p.quantity <= threshold]
        low.sort(key=lambda p: (p.quantity, p.name.casefold()))
        return {
            "threshold": threshold,
            "total_matching": len(low),
            "products": [product_summary(p) for p in low[:limit]],
        }

    @mcp.tool()
    async def get_inventory_summary(threshold: int = 3) -> dict:
        """Summarize stock units, out-of-stock products, and low-stock products."""
        if threshold < 0:
            raise ValueError("threshold cannot be negative")
        async with StoreClient() as client:
            products = await client.products()
        known = [p for p in products if p.quantity is not None]
        return {
            "product_count": len(products),
            "listed_product_count": sum(p.isListed is True for p in products),
            "stock_units": sum(max(0, p.quantity or 0) for p in known),
            "out_of_stock_count": sum(p.quantity == 0 for p in known),
            "low_stock_count": sum(p.quantity is not None and 0 < p.quantity <= threshold for p in products),
            "unknown_stock_count": len(products) - len(known),
            "low_stock_threshold": threshold,
        }
