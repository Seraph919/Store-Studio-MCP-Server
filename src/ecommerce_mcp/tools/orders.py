"""Seller order queries; backend scope: orders:read."""

from __future__ import annotations

from mcp.server import MCPServer

from ecommerce_mcp.clients.store_client import StoreClient
from ecommerce_mcp.models.schemas import money, order_summary


VALID_STATUSES = {"PENDING", "CONFIRMED", "NO_ANSWER", "PROCESSING", "SHIPPED", "DELIVERED", "CANCELLED"}


def register_order_tools(mcp: MCPServer) -> None:
    @mcp.tool()
    async def list_orders(status: str = "", limit: int = 30) -> dict:
        """List recent seller orders, optionally filtered by status (e.g. PENDING). Excludes customer contact details."""
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        normalized = status.strip().upper()
        if normalized and normalized not in VALID_STATUSES:
            raise ValueError(f"Invalid status. Choose one of: {', '.join(sorted(VALID_STATUSES))}")
        async with StoreClient() as client:
            orders = await client.orders()
        if normalized:
            orders = [o for o in orders if (o.status or "PENDING").upper() == normalized]
        orders.sort(key=lambda o: o.createdAt.isoformat() if o.createdAt else "", reverse=True)
        return {"total_matching": len(orders), "orders": [order_summary(o) for o in orders[:limit]]}

    @mcp.tool()
    async def get_order_details(seller_order_id: int) -> dict:
        """Get one seller order with items, delivery contact and address for fulfillment. This returns private customer data."""
        async with StoreClient() as client:
            orders = await client.orders()
        order = next((o for o in orders if o.id == seller_order_id), None)
        if order is None:
            return {"found": False, "seller_order_id": seller_order_id}
        return {
            "found": True,
            "order": {
                **order_summary(order),
                "customer": {
                    "name": order.customerName,
                    "email": order.customerEmail,
                    "phone": order.phoneNumber,
                    "shipping_address": order.shippingAddress,
                    "city": order.city,
                },
                "items": [
                    {
                        "product_id": item.productId,
                        "name": item.productName,
                        "quantity": item.quantity,
                        "unit_price": money(item.unitPrice),
                        "subtotal": money(item.subtotal),
                    }
                    for item in order.items
                ],
            },
        }
