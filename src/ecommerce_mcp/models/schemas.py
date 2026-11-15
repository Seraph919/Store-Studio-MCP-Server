"""Subset of actual Spring Boot DTOs returned by /api/v1/mcp/*.

The API uses camelCase. Our tool responses are intentionally smaller and use
snake_case, avoiding unnecessary disclosure of order/customer information.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class StoreModel(BaseModel):
    model_config = ConfigDict(extra="ignore")


class Product(StoreModel):
    id: int
    name: str
    description: str | None = None
    price: Decimal | None = None
    quantity: int | None = None
    categoryName: str | None = None
    isListed: bool | None = None


class OrderItem(StoreModel):
    id: int | None = None
    productId: int | None = None
    productName: str | None = None
    quantity: int | None = None
    unitPrice: Decimal | None = None
    subtotal: Decimal | None = None


class SellerOrder(StoreModel):
    # 'id' is the seller-order ID, distinct from the parent orderId.
    id: int
    orderId: int | None = None
    publicOrderReference: str | None = None
    status: str | None = None
    subtotal: Decimal | None = None
    createdAt: datetime | None = None
    updatedAt: datetime | None = None
    customerName: str | None = None
    customerEmail: str | None = None
    phoneNumber: str | None = None
    shippingAddress: str | None = None
    city: str | None = None
    items: list[OrderItem] = Field(default_factory=list)


class SellerKpis(StoreModel):
    pendingCallConfirmationsCount: int = 0
    todayRevenue: Decimal = Decimal("0")
    monthRevenue: Decimal = Decimal("0")
    ordersByStatus: dict[str, int] = Field(default_factory=dict)
    lowStockProducts: list[Product] = Field(default_factory=list)


class StoreSettings(StoreModel):
    storeName: str | None = None
    storeTagline: str | None = None
    shippingMode: str | None = None
    shippingFee: Decimal | None = None
    freeShippingThreshold: Decimal | None = None
    heroTitle: str | None = None
    heroIntro: str | None = None
    phone: str | None = None
    email: str | None = None
    updatedAt: datetime | None = None


def money(amount: Decimal | None) -> str:
    """Keep decimal precision; never silently convert prices to floats."""
    return str(amount if amount is not None else Decimal("0"))


def utc_datetime(moment: datetime | None) -> datetime | None:
    if moment is None:
        return None
    if moment.tzinfo is None:
        # Spring Boot DTO uses Instant (UTC); tolerate naive test fixtures.
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def product_summary(product: Product) -> dict:
    return {
        "id": product.id,
        "name": product.name,
        "price": money(product.price),
        "stock_quantity": product.quantity,
        "category": product.categoryName,
        "is_listed": product.isListed,
    }


def order_summary(order: SellerOrder) -> dict:
    return {
        "seller_order_id": order.id,
        "order_id": order.orderId,
        "reference": order.publicOrderReference,
        "status": order.status,
        "subtotal": money(order.subtotal),
        "created_at_utc": utc_datetime(order.createdAt).isoformat() if order.createdAt else None,
        "item_count": sum(item.quantity or 0 for item in order.items),
    }
