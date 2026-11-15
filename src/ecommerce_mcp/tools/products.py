"""Seller catalog queries; backend scope: products:read."""

from __future__ import annotations

from mcp.server import MCPServer

from ecommerce_mcp.clients.store_client import StoreClient
from ecommerce_mcp.models.schemas import product_summary


def register_product_tools(mcp: MCPServer) -> None:
    @mcp.tool()
    async def list_products(search: str = "", listed_only: bool = False, limit: int = 50) -> dict:
        """Search the seller's product catalog by name; optionally show listed products only."""
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        async with StoreClient() as client:
            products = await client.products()
        query = search.strip().casefold()
        filtered = [
            p for p in products
            if (not query or query in p.name.casefold())
            and (not listed_only or p.isListed is True)
        ]
        return {"total_matching": len(filtered), "products": [product_summary(p) for p in filtered[:limit]]}

    @mcp.tool()
    async def get_product(product_id: int) -> dict:
        """Get a product's details, pricing, stock, and listing status by product ID."""
        async with StoreClient() as client:
            products = await client.products()
        item = next((p for p in products if p.id == product_id), None)
        if item is None:
            return {"found": False, "product_id": product_id}
        return {"found": True, "product": {**product_summary(item), "description": item.description}}
