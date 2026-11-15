"""HTTP contracts exercised without a running Spring Boot backend."""

import httpx
import pytest

from ecommerce_mcp.clients.store_client import StoreAPIError, StoreClient
from ecommerce_mcp.config import Settings


SETTINGS = Settings("https://shop.example.test", "store_sk_unit_test")


@pytest.mark.asyncio
async def test_uses_api_key_and_decodes_orders():
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/mcp/orders"
        assert request.headers["X-API-Key"] == "store_sk_unit_test"
        return httpx.Response(
            200,
            json=[{
                "id": 17, "orderId": 84, "status": "PENDING",
                "subtotal": 120.50, "createdAt": "2026-11-08T15:00:00Z",
                "customerName": "Example Customer", "items": [
                    {"productId": 1, "productName": "Mug", "quantity": 2,
                     "unitPrice": 60.25, "subtotal": 120.50}
                ],
            }],
        )

    async with StoreClient(settings=SETTINGS, transport=httpx.MockTransport(respond)) as client:
        orders = await client.orders()
    assert len(orders) == 1
    assert orders[0].id == 17
    assert str(orders[0].subtotal) == "120.5"
    assert orders[0].items[0].productName == "Mug"


@pytest.mark.asyncio
@pytest.mark.parametrize("status, fragment", [
    (401, "invalid"), (403, "permission"), (500, "HTTP 500"),
])
async def test_http_errors_are_clear_and_do_not_expose_key(status, fragment):
    async with StoreClient(
        settings=SETTINGS,
        transport=httpx.MockTransport(lambda request: httpx.Response(status)),
    ) as client:
        with pytest.raises(StoreAPIError) as exc:
            await client.products()
    message = str(exc.value)
    assert fragment in message
    assert "store_sk_unit_test" not in message


@pytest.mark.asyncio
async def test_unexpected_json_response_is_rejected():
    async with StoreClient(
        settings=SETTINGS,
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"not": "a list"})),
    ) as client:
        with pytest.raises(StoreAPIError, match="Unexpected products response structure"):
            await client.products()


@pytest.mark.asyncio
async def test_http_redirect_is_not_followed_with_key():
    async with StoreClient(
        settings=SETTINGS,
        transport=httpx.MockTransport(lambda request: httpx.Response(302, headers={"Location": "https://other.example"})),
    ) as client:
        with pytest.raises(StoreAPIError, match="HTTP 302"):
            await client.orders()
