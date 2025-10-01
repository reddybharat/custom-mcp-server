# Custom MCP Server & Client

A demonstration of the Model Context Protocol (MCP) architecture with custom servers and a ReAct agent client. This project showcases how to build modular, tool-based AI systems using MCP.

## What is MCP?

The Model Context Protocol (MCP) is a standard for connecting AI models to external tools and data sources. It enables:

- **Modular Architecture**: Separate tools into independent servers
- **Tool Discovery**: Automatic tool registration and discovery
- **Multiple Transports**: Support for stdio, HTTP, and other communication methods
- **Type Safety**: Strongly typed tool definitions with automatic validation

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐
│   ReAct Agent   │    │  Calculator     │
│   (Client)      │◄──►│  Server         │
│                 │    │  (stdio)        │
└─────────────────┘    └─────────────────┘
         │
         │ HTTP
         ▼
┌─────────────────┐
│   Weather       │
│   Server        │
│   (HTTP)        │
└─────────────────┘
```

## Project Structure

```
custom-mcp-server/
├── client.py              # ReAct agent client
├── server/
│   ├── calculator.py      # Calculator MCP server (stdio)
│   └── weather.py         # Weather MCP server (HTTP)
├── requirements.txt       # Dependencies
└── pyproject.toml        # Project configuration
```

## Key Components

### 1. MCP Servers

**Calculator Server** (`server/calculator.py`):
- Uses `stdio` transport for direct communication
- Provides basic math operations: add, subtract, multiply, divide
- Demonstrates simple tool definition with FastMCP

**Weather Server** (`server/weather.py`):
- Uses `streamable-http` transport for web communication
- Integrates with external weather API
- Shows async tool implementation

### 2. MCP Client

**ReAct Agent** (`client.py`):
- Connects to multiple MCP servers simultaneously
- Uses LangGraph's ReAct agent for tool orchestration
- Demonstrates multi-server tool integration

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**:
   ```bash
   export GROQ_API_KEY="your-groq-api-key"
   export WEATHER_API_KEY="your-weather-api-key"
   ```

3. **Run the Weather Server** (in one terminal):
   ```bash
   python server/weather.py
   ```

4. **Run the Client** (in another terminal):
   ```bash
   python client.py
   ```

## MCP Learning Points

### Server Development
- **FastMCP**: Simplifies MCP server creation with decorators
- **Tool Definition**: Use type hints and docstrings for automatic schema generation
- **Transport Selection**: Choose between stdio, HTTP, or other transports based on use case

### Client Development
- **Multi-Server Support**: Connect to multiple MCP servers simultaneously
- **Tool Discovery**: Automatic tool registration from connected servers
- **Agent Integration**: Use with LangGraph, LangChain, or other agent frameworks

### Best Practices
- **Type Safety**: Always use type hints for better tool validation
- **Error Handling**: Implement proper error handling in tools
- **Documentation**: Write clear docstrings for tool descriptions
- **Transport Choice**: Use stdio for local tools, HTTP for distributed systems
