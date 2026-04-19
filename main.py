from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI

from server.math import math_mcp
from server.weather import weather_mcp
import uvicorn

# Mounted Starlette apps do not run their own lifespan under FastAPI; FastMCP
# needs session_manager.run() for the Streamable HTTP task group.
_MCPS = (math_mcp, weather_mcp)

math_starlette = math_mcp.streamable_http_app()
weather_starlette = weather_mcp.streamable_http_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:
        for mcp in _MCPS:
            await stack.enter_async_context(mcp.session_manager.run())
        yield


app = FastAPI(title="Custom MCP Server", lifespan=lifespan)

app.mount("/math", math_starlette)
app.mount("/weather", weather_starlette)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
