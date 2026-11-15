# E-commerce Operations MCP Server (Python)

A read-only MCP server using the **official Python MCP SDK v2**. It connects to the
Spring Boot backend from the modified `Ecomm-platform-mcp-api-keys.zip` project.

## Requirements

- Python 3.11+
- Running Spring Boot store backend with the `V6__mcp_api_keys.sql` migration applied
- A seller-generated API key with these **read-only scopes**:
  `orders:read`, `products:read`, `analytics:read`, and `settings:read`

No `pyproject.toml` or `uv` required.

## Get started

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Generate a key in the seller dashboard (`/seller/api-keys`) and put it in `.env`.
The token is displayed only once. **Never commit `.env` or paste your token into chats.**

Run the MCP server (uses `stdio`, so it normally prints nothing):

```bash
python src/ecommerce_mcp/server.py
```

Test tools in the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector python src/ecommerce_mcp/server.py
```

Or using the SDK CLI:

```bash
mcp dev src/ecommerce_mcp/server.py
```

Connect in Inspector, select Tools → List Tools, then run `list_orders`.
The backend must be running at `STORE_API_URL` for the tools to succeed.

## Available tools (12)

| Module | Tools | Required scope |
|---|---|---|
| Orders | `list_orders`, `get_order_details` | `orders:read` |
| Products | `list_products`, `get_product` | `products:read` |
| Inventory | `get_low_stock_products`, `get_inventory_summary` | `products:read` |
| Analytics | `get_sales_summary` | `analytics:read` |
| Analytics | `get_best_sellers`, `compare_sales` | `orders:read` |
| Analytics | `get_daily_briefing` | `analytics:read`, `orders:read`, `products:read` |
| Settings | `get_store_settings`, `get_shipping_settings` | `settings:read` |

Examples:

- `list_orders(status="PENDING", limit=20)`
- `get_order_details(seller_order_id=15)` — includes customer information for fulfillment
- `get_low_stock_products(threshold=3)`
- `get_best_sellers(days=30, limit=10)`
- `get_daily_briefing()`

## Backend integration

The MCP server calls only the four endpoints actually available in your modified
Spring Boot app. Every call uses `X-API-Key: <key>`.

| Endpoint | Returns |
|---|---|
| `GET /api/v1/mcp/orders` | Seller order objects and item lines |
| `GET /api/v1/mcp/products` | Seller catalog and available quantities |
| `GET /api/v1/mcp/analytics` | Seller KPIs, today/month revenue, order status counts |
| `GET /api/v1/mcp/settings` | Storefront and shipping settings |

Inventory, best sellers, period comparisons, and daily briefings are calculated
**in Python** from these endpoints, so **no additional Spring Boot endpoints** are
required. All tools are **read-only**; they do not modify order status or prices.

### Important accuracy notes

- The backend reports `todayRevenue`/`monthRevenue` based on **UTC** dates and
  non-cancelled order **subtotals**, not necessarily collected/paid revenue.
- The backend does not expose a currency field; the MCP server returns decimal
  monetary amounts as **strings** and does not assume MAD/USD.
- The order endpoint returns **all orders** for the seller. `limit`, `status`, and
  time-based analytics filtering are applied locally by the MCP server. For a
  very large store, add backend pagination and server-side filtering later.
- `get_order_details` can reveal a customer's name, contact information, and
  shipping address to the connected AI client. Use only with authorized sellers.
- Only the `get_order_details` tool returns customer contact information; order
  lists and reports intentionally omit it.

## Troubleshooting

- `401`: API key was not accepted (missing, revoked, invalid, or expired).
- `403`: API key lacks a requested scope.
- `Store API unreachable`: check backend port and the `STORE_API_URL` origin.
- `.env` not found: copy `.env.example` and add your real API key.
- Remote `http://` is rejected by default to avoid leaking permanent credentials.
  Use HTTPS. For an isolated Docker network, explicitly set
  `STORE_ALLOW_INSECURE_HTTP=true` after verifying the network is trusted.

## Run offline tests

```bash
pip install pytest pytest-asyncio
PYTHONPATH=src pytest -q
```
