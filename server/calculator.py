from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Calculator")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers and return the result
    """
    return a + b

@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers and return the result
    """
    return a - b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers and return the result
    """
    return a * b

@mcp.tool()
def divide(a: int, b: int) -> int:
    """Divide two numbers and return the result
    """
    return a / b


if __name__ == "__main__":
    mcp.run(transport="stdio")