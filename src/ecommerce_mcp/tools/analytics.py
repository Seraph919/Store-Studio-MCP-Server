"""Seller metrics: backend-provided KPIs plus transparent order-based calculations."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from mcp.server import MCPServer

from ecommerce_mcp.clients.store_client import StoreClient
from ecommerce_mcp.models.schemas import SellerOrder, money, product_summary, utc_datetime


def in_period(order: SellerOrder, start: datetime, end: datetime) -> bool:
    when = utc_datetime(order.createdAt)
    return when is not None and start <= when < end and (order.status or "").upper() != "CANCELLED"


def revenue_for(orders: list[SellerOrder], start: datetime, end: datetime) -> tuple[Decimal, int]:
    selected = [o for o in orders if in_period(o, start, end)]
    return sum((o.subtotal or Decimal("0") for o in selected), Decimal("0")), len(selected)


def register_analytics_tools(mcp: MCPServer) -> None:
    @mcp.tool()
    async def get_sales_summary() -> dict:
        """Get backend-calculated today's and this month's UTC order revenue and status counts."""
        async with StoreClient() as client:
            kpis = await client.analytics()
        return {
            "today_revenue": money(kpis.todayRevenue),
            "month_revenue": money(kpis.monthRevenue),
            "orders_by_status": kpis.ordersByStatus,
            "pending_confirmations": kpis.pendingCallConfirmationsCount,
            "low_stock_count_at_threshold_3": len(kpis.lowStockProducts),
            "note": "Revenue is order subtotal excluding CANCELLED; it is not necessarily collected payments. Backend uses UTC calendar boundaries. Currency is store-dependent.",
        }

    @mcp.tool()
    async def get_best_sellers(days: int = 30, limit: int = 10) -> dict:
        """Rank products by units sold in a rolling UTC period, excluding cancelled seller orders."""
        if not 1 <= days <= 365:
            raise ValueError("days must be between 1 and 365")
        if not 1 <= limit <= 30:
            raise ValueError("limit must be between 1 and 30")
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        async with StoreClient() as client:
            orders = await client.orders()
        totals = defaultdict(lambda: {"units_sold": 0, "item_revenue": Decimal("0"), "name": None})
        for order in orders:
            if not in_period(order, start, end):
                continue
            for item in order.items:
                key = item.productId if item.productId is not None else f"unlinked:{item.productName or 'unknown'}"
                aggregate = totals[key]
                aggregate["units_sold"] += item.quantity or 0
                aggregate["item_revenue"] += item.subtotal or (
                    (item.unitPrice or Decimal("0")) * (item.quantity or 0)
                )
                aggregate["name"] = item.productName or aggregate["name"]
        top = sorted(totals.items(), key=lambda entry: entry[1]["units_sold"], reverse=True)
        return {
            "days": days,
            "time_basis": "rolling UTC days",
            "total_distinct_products": len(top),
            "products": [
                {
                    "product_id": key if isinstance(key, int) else None,
                    "name": info["name"],
                    "units_sold": info["units_sold"],
                    "item_revenue": money(info["item_revenue"]),
                }
                for key, info in top[:limit]
            ],
        }

    @mcp.tool()
    async def compare_sales(days: int = 7) -> dict:
        """Compare seller order subtotals over the latest N days against the prior equal-length UTC period."""
        if not 1 <= days <= 180:
            raise ValueError("days must be between 1 and 180")
        end = datetime.now(timezone.utc)
        middle = end - timedelta(days=days)
        start = middle - timedelta(days=days)
        async with StoreClient() as client:
            orders = await client.orders()
        current, current_count = revenue_for(orders, middle, end)
        previous, previous_count = revenue_for(orders, start, middle)
        change = money((current - previous) / previous * 100) if previous != 0 else None
        return {
            "period_days": days,
            "time_basis": "rolling UTC days",
            "current_period": {"revenue": money(current), "order_count": current_count},
            "previous_period": {"revenue": money(previous), "order_count": previous_count},
            "revenue_change_percent": change,
            "note": "Percent change is null when previous revenue is zero. Revenue uses non-cancelled order subtotals, not verified payments.",
        }

    @mcp.tool()
    async def get_daily_briefing() -> dict:
        """Daily seller overview: today's UTC revenue, order activity, pending work, and stock alerts."""
        async with StoreClient() as client:
            kpis, products, orders = await asyncio.gather(client.analytics(), client.products(), client.orders())
        now = datetime.now(timezone.utc)
        today = now.date()
        today_orders = [o for o in orders if (dt := utc_datetime(o.createdAt)) and dt.date() == today]
        return {
            "date_utc": today.isoformat(),
            "today_revenue": money(kpis.todayRevenue),
            "month_revenue": money(kpis.monthRevenue),
            "today_order_count": len(today_orders),
            "today_pending_orders": sum((o.status or "PENDING").upper() == "PENDING" for o in today_orders),
            "total_pending_confirmations": kpis.pendingCallConfirmationsCount,
            "orders_by_status": kpis.ordersByStatus,
            "out_of_stock_products": sum(p.quantity == 0 for p in products),
            "low_stock_products_at_3_or_less": [
                product_summary(p) for p in sorted(
                    (p for p in products if p.quantity is not None and p.quantity <= 3),
                    key=lambda p: p.quantity,
                )[:10]
            ],
            "note": "UTC dates; subtotal-based revenue excludes cancellations but is not guaranteed paid revenue. Up to 10 stock alerts shown.",
        }
