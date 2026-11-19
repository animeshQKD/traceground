"""Check the demo's MCP server: connect to it as an MCP client, list its tools, and call traceground_check
twice (an answer with a wrong number, and a correct one).

    python space/app.py              # in one terminal: starts the page and the MCP server
    python space/mcp_check.py        # in another; or give the URL: python space/mcp_check.py http://...

Needs the mcp package, which comes with gradio[mcp]."""
import asyncio
import json
import sys

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

URL = "http://127.0.0.1:7860/gradio_api/mcp/"


async def main(url: str) -> int:
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools
            print("Tools:", ", ".join(t.name for t in tools))
            for answer, expected in (("Revenue was 5 million.", "problems"), ("Revenue was 4 million.", "ok")):
                res = await session.call_tool("traceground_check", {"answer": answer,
                                                                    "sources": "[S1] Revenue was 4 million."})
                report = json.loads(res.content[0].text)
                print(f"{answer!r}: {report['verdict']} ({report['summary']})")
                if report["verdict"] != expected:
                    print(f"  expected {expected}")
                    return 1
    print("MCP server works.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else URL)))
