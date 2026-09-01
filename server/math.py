from typing import List

from mcp.server.fastmcp import FastMCP

math_mcp = FastMCP("Math")


@math_mcp.tool()
async def add_tool(numbers: List[float]) -> float:
    """use this tool to perform addition of a list of numbers"""
    return sum(numbers)


@math_mcp.tool()
async def substract_tool(a: float, b: float) -> float:
    """use this tool to perform substraction between two numbers"""
    return a - b


@math_mcp.tool()
async def multiply_tool(numbers: List[float]) -> float:
    """use this tool to perform multiplication of a list of numbers"""
    result = 1
    for num in numbers:
        result *= num
    return result


@math_mcp.tool()
async def divide_tool(a: float, b: float) -> float:
    """use this tool to perform division between two numbers"""
    return a / b


@math_mcp.resource("resource://math/capabilities", mime_type="text/plain")
async def math_capabilities() -> str:
    """Reference text describing Math MCP tools (for clients that load resources)."""
    return (
        "Math MCP tools:\n"
        "- add_tool(numbers: list[float]) -> float: sum of numbers\n"
        "- substract_tool(a, b) -> float: a minus b\n"
        "- multiply_tool(numbers: list[float]) -> float: product\n"
        "- divide_tool(a, b) -> float: a divided by b (b must be non-zero)\n"
    )


@math_mcp.prompt(
    name="math_assistant",
    title="Math assistant",
    description="Bootstrap messages for math-focused tasks; optional focus hint.",
)
async def math_assistant(focus: str = "general") -> str:
    return (
        "You are helping with numeric calculations via the Math MCP server. "
        f"User focus: {focus}. "
        "Use add_tool for sums, substract_tool for a−b, multiply_tool for products, "
        "and divide_tool for division. Prefer tools over mental arithmetic for accuracy."
    )
