"""MCP server entry point. Run directly with `python src/ecommerce_mcp/server.py`."""

from __future__ import annotations

if __package__ in {"", None}:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp.server import MCPServer

from ecommerce_mcp.tools.analytics import register_analytics_tools
from ecommerce_mcp.tools.inventory import register_inventory_tools
from ecommerce_mcp.tools.orders import register_order_tools
from ecommerce_mcp.tools.products import register_product_tools
from ecommerce_mcp.tools.settings import register_settings_tools
from ecommerce_mcp.prompts.seller import register_seller_prompts


mcp = MCPServer(
    "ecommerce-operations",
    instructions=(
        "Read-only seller tools backed by the configured store. "
        "Do not claim order revenue is paid revenue. "
        "Customer contact information is available only through get_order_details; "
        "request it only when needed for a specific fulfillment task. "
        "Amounts have no guaranteed currency in the current API."
    ),
)

register_order_tools(mcp)
register_product_tools(mcp)
register_inventory_tools(mcp)
register_analytics_tools(mcp)
register_settings_tools(mcp)
register_seller_prompts(mcp)


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8000,
        stateless_http=True,
        json_response=True,
    )
