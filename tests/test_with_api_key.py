#!/usr/bin/env python3
"""Integration test script.

Intent:
    Test the MCP YouTube Extract server end-to-end using a real API key.

Test environment note:
    Requires optional `mcp` dependency and network access.
    Skipped automatically when `mcp` is unavailable.
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


async def test_server_with_api_key():
    """Test the MCP YouTube Extract server with real API key."""

    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        print("❌ YOUTUBE_API_KEY not found in .env file")
        return

    env = os.environ.copy()
    env["YOUTUBE_API_KEY"] = api_key

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "youtube_mcp.server"],
        env=env,
    )

    print("🔍 Testing MCP YouTube Extract server with API key...")

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("✅ Connected successfully!")

                await session.initialize()
                print("✅ Session initialized!")

                test_cases = [
                    {
                        "name": "Rick Astley - Never Gonna Give You Up (popular music video)",
                        "video_id": "dQw4w9WgXcQ",
                        "expect_transcript": True,
                    },
                    {
                        "name": "TED Talk (should have transcript)",
                        "video_id": "ZQUxL4Jm1Lo",
                        "expect_transcript": True,
                    },
                    {
                        "name": "Short video test",
                        "video_id": "jNQXAC9IVRw",
                        "expect_transcript": False,
                    },
                ]

                for i, test_case in enumerate(test_cases, 1):
                    print(f"\n🧪 Test {i}: {test_case['name']}")
                    print(f"   Video ID: {test_case['video_id']}")

                    try:
                        result = await session.call_tool(
                            "get_yt_video_info", {"video_id": test_case["video_id"]}
                        )

                        if hasattr(result, "content"):
                            content_text = ""
                            for content in result.content:
                                if hasattr(content, "text"):
                                    content_text += content.text
                                else:
                                    content_text += str(content)

                            print("✅ Tool executed successfully!")
                            print(f"   Response length: {len(content_text)}")
                        else:
                            print(f"Raw result: {result}")

                    except Exception as e:
                        print(f"Error: {e}")

    except Exception as e:
        print(f"Connection error: {e}")


if __name__ == "__main__":
    asyncio.run(test_server_with_api_key())
