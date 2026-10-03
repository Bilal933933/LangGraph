"""خادم MCP تجريبي بـ FastMCP للربط مع OpenCode."""

from fastmcp import FastMCP

mcp = FastMCP("demo-server")


@mcp.tool
def add(a: int, b: int) -> int:
    """جمع رقمين."""
    return a + b


@mcp.resource("config://app")
def get_config() -> str:
    """إعدادات التطبيق (مورد ثابت)."""
    return "app_name=langgraph-lab\ndebug=true"


@mcp.resource("greet://{name}")
def greet(name: str) -> str:
    """تحية شخصية (قالب مورد ديناميكي)."""
    return f"مرحباً {name}!"


if __name__ == "__main__":
    mcp.run()
