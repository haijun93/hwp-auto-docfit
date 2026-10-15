import importlib.util
import sys
import unittest
from pathlib import Path


@unittest.skipUnless(importlib.util.find_spec("mcp"), "optional MCP SDK is not installed")
class McpStdioProtocolTests(unittest.TestCase):
    def test_stdio_server_lists_generation_tools(self):
        import anyio
        from mcp import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client

        repo_root = Path(__file__).resolve().parents[1]
        parameters = StdioServerParameters(
            command=sys.executable,
            args=[str(repo_root / "scripts" / "mcp_server.py")],
            cwd=repo_root,
        )

        async def check_tools():
            async with stdio_client(parameters) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.list_tools()
                    return {tool.name for tool in result.tools}

        names = anyio.run(check_tools)
        self.assertEqual(names, {"list_format_presets", "create_document_from_ai_answer"})


if __name__ == "__main__":
    unittest.main()
