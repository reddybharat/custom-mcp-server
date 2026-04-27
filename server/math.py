from typing import List

from server.core.auth import create_authenticated_mcp

math_mcp = create_authenticated_mcp("Math", "math", required_scopes=["mcp:math"])


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
