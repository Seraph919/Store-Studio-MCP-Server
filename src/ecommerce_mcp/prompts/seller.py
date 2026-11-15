
from mcp.server import MCPServer


def register_seller_prompts(mcp: MCPServer):

    @mcp.prompt()
    def daily_store_review() -> str:
        """Analyze today's store performance."""
        return """
        Use get_daily_briefing to analyze my store today.

        Explain:
        - Today's sales and orders
        - Pending orders requiring attention
        - Products running low on stock
        - Recommended actions

        Keep the summary short and actionable.
        Do not invent unavailable metrics.
        """

    @mcp.prompt()
    def inventory_review(threshold: str = "5") -> str:
        """Review inventory and recommend restocking."""
        return f"""
        Use get_low_stock_products with threshold {threshold}.

        Identify:
        - Products requiring restocking
        - Products with zero inventory
        - Suggested restocking priorities

        Do not invent demand forecasts.
        """

    @mcp.prompt()
    def sales_report(period: str = "7 days") -> str:
        """Generate a seller sales performance report."""
        return f"""
        Analyze my store's sales over the last {period}.

        Use available sales analytics tools.

        Report:
        - Revenue and order counts
        - Best-selling products
        - Sales trends
        - Opportunities for improvement

        Explain any missing data or limitations.
        """
