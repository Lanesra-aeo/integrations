"""The same first call, through the official MCP Python SDK (version 2) instead of plain HTTP.

    pip install -r requirements-sdk.txt
    export LANESRA_API_KEY=lns_live_your_key_here
    python mcp_sdk.py

Use this when you already build on the SDK, for example inside an agent framework.
The key travels as a header on the HTTP client the transport uses.
"""

import asyncio
import json
import os

from mcp import Client
from mcp.client.streamable_http import create_mcp_http_client, streamable_http_client

URL = os.environ.get("LANESRA_MCP_URL", "https://app.lanesra.ai/mcp")


async def main():
    headers = {"Authorization": f"Bearer {os.environ['LANESRA_API_KEY']}"}
    async with create_mcp_http_client(headers=headers) as http:
        async with Client(streamable_http_client(URL, http_client=http)) as client:
            tools = await client.list_tools()
            print(f"{len(tools.tools)} tools:", ", ".join(t.name for t in tools.tools))

            result = await client.call_tool("get_visibility_overview", {})
            text = result.content[0].text
            if result.is_error:
                raise SystemExit(text)
            overview = json.loads(text)
            own = overview.get("own") or {}
            print(f"{overview['brand']}: visibility {own.get('visibility')}% (captured {overview['capturedAt'] or 'not yet'})")


if __name__ == "__main__":
    asyncio.run(main())
