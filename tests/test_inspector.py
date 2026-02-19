#!/usr/bin/env python3
"""Integration test script.

Intent:
    Inspect the MCP server tools and schemas via stdio transport.

Test environment note:
    Requires optional `mcp` dependency. Skipped when unavailable.
"""

import asyncio
import os
import sys

import pytest
from dotenv import load_dotenv

pytest.importorskip("mcp")
from mcp import ClientSession, StdioServerParameters  # type: ignore  # noqa: E402
from mcp.client.stdio import stdio_client  # type: ignore  # noqa: E402

# Load environment variables from .env file
load_dotenv()


async def inspect_server():
    """Inspect the MCP YouTube Extract server."""

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "youtube_mcp.server"],
        env=os.environ.copy(),
    )

    print("🔍 Connecting to MCP YouTube Extract server...")

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("✅ Connected successfully!")

                await session.initialize()
                print("✅ Session initialized!")

                print("\n📋 Available tools:")
                tools_result = await session.list_tools()
                if hasattr(tools_result, "tools"):
                    for tool in tools_result.tools:
                        print(f"  • {tool.name}: {tool.description}")
                        if hasattr(tool, "inputSchema") and tool.inputSchema:
                            schema = tool.inputSchema
                            if "properties" in schema:
                                print("    Parameters:")
                                for param, details in schema["properties"].items():
                                    required = param in schema.get("required", [])
                                    print(
                                        f"      - {param}: {details.get('description', 'No description')} "
                                        f"{'(required)' if required else ''}"
                                    )
                else:
                    print("  No tools found")

                print("\n✅ Inspector completed")

    except Exception as e:
        print(f"Connection error: {e}")


if __name__ == "__main__":
    asyncio.run(inspect_server())
