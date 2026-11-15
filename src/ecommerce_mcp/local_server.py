import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from mcp.server import MCPServer

from ecommerce_mcp.tools.orders import register_order_tools
from ecommerce_mcp.tools.products import register_product_tools
from ecommerce_mcp.tools.inventory import register_inventory_tools
from ecommerce_mcp.tools.analytics import register_analytics_tools
from ecommerce_mcp.tools.settings import register_settings_tools
from ecommerce_mcp.prompts.seller import register_seller_prompts

mcp = MCPServer("ecommerce-operations-local")

register_order_tools(mcp)
register_product_tools(mcp)
register_inventory_tools(mcp)
register_analytics_tools(mcp)
register_settings_tools(mcp)
register_seller_prompts(mcp)

if __name__ == "__main__":
    mcp.run(transport="stdio")
