"""Behavior of the registered tool functions using in-memory Spring Boot DTOs."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

pytest.importorskip("mcp.server")

from ecommerce_mcp.models.schemas import Product, SellerKpis, SellerOrder, StoreSettings
from ecommerce_mcp.tools import orders as orders_mod, inventory as inventory_mod, analytics as analytics_mod


class Registry:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorate(func):
            self.tools[func.__name__] = func
            return func
        return decorate


class MockClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        pass

    async def orders(self):
        now = datetime.now(timezone.utc) - timedelta(minutes=1)
        return [
            SellerOrder.model_validate({
                "id": 1, "status": "PENDING", "subtotal": "50.00", "createdAt": now.isoformat(),
                "customerName": "Customer", "phoneNumber": "111", "items": [
                    {"productId": 9, "productName": "Mug", "quantity": 2, "subtotal": "50.00"}
                ],
            }),
            SellerOrder.model_validate({
                "id": 2, "status": "CANCELLED", "subtotal": "999.00", "createdAt": now.isoformat(),
                "items": [{"productId": 9, "productName": "Mug", "quantity": 100, "subtotal": "999"}],
            }),
            SellerOrder.model_validate({
                "id": 3, "status": "SHIPPED", "subtotal": "30.00",
                "createdAt": (now - timedelta(days=8)).isoformat(),
                "items": [{"productId": 8, "productName": "Tee", "quantity": 1, "subtotal": "30"}],
            }),
        ]

    async def products(self):
        return [
            Product(id=9, name="Mug", quantity=2, price=Decimal("25.00")),
            Product(id=8, name="Tee", quantity=0, price=Decimal("30.00")),
        ]

    async def analytics(self):
        return SellerKpis(todayRevenue=Decimal("50"), monthRevenue=Decimal("80"),
                          pendingCallConfirmationsCount=1, ordersByStatus={"PENDING": 1})

    async def settings(self):
        return StoreSettings(storeName="Example", shippingFee=Decimal("10"))


@pytest.fixture
def funcs(monkeypatch):
    for mod in (orders_mod, inventory_mod, analytics_mod):
        monkeypatch.setattr(mod, "StoreClient", MockClient)
    register = Registry()
    orders_mod.register_order_tools(register)
    inventory_mod.register_inventory_tools(register)
    analytics_mod.register_analytics_tools(register)
    return register.tools


@pytest.mark.asyncio
async def test_order_list_excludes_customer_pii(funcs):
    result = await funcs["list_orders"](status="pending")
    assert result["total_matching"] == 1
    assert "customer" not in result["orders"][0]


@pytest.mark.asyncio
async def test_order_details_include_fulfillment_info(funcs):
    result = await funcs["get_order_details"](seller_order_id=1)
    assert result["found"] is True
    assert result["order"]["customer"]["name"] == "Customer"


@pytest.mark.asyncio
async def test_low_stock_includes_zero(funcs):
    result = await funcs["get_low_stock_products"](threshold=3)
    assert [p["id"] for p in result["products"]] == [8, 9]


@pytest.mark.asyncio
async def test_best_seller_excludes_cancelled(funcs):
    result = await funcs["get_best_sellers"](days=7)
    assert result["products"][0]["units_sold"] == 2
    assert result["products"][0]["item_revenue"] == "50.00"


@pytest.mark.asyncio
async def test_comparison_previous_period(funcs):
    result = await funcs["compare_sales"](days=7)
    assert result["current_period"]["revenue"] == "50.00"
    assert result["previous_period"]["revenue"] == "30.00"


@pytest.mark.asyncio
async def test_daily_briefing(funcs):
    result = await funcs["get_daily_briefing"]()
    assert result["today_order_count"] == 2
    assert result["today_pending_orders"] == 1
    assert result["out_of_stock_products"] == 1
