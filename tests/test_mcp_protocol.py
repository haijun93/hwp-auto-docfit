import importlib.util
import os
import subprocess
import sys
import unittest
from pathlib import Path


@unittest.skipUnless(importlib.util.find_spec("mcp"), "optional MCP SDK is not installed")
class McpStdioProtocolTests(unittest.TestCase):
    def test_server_is_disabled_without_explicit_opt_in(self):
        repo_root = Path(__file__).resolve().parents[1]
        env = os.environ.copy()
        env.pop("DOCFIT_MCP_ENABLED", None)
        result = subprocess.run(
            [sys.executable, str(repo_root / "scripts" / "mcp_server.py")],
            cwd=repo_root,
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 3)
        self.assertIn("disabled by default", result.stderr)

    def test_stdio_server_lists_generation_tools(self):
        import anyio
        from mcp import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client

        repo_root = Path(__file__).resolve().parents[1]
        server_script = repo_root / "scripts" / "mcp_server.py"
        launcher = (
            "import os, runpy, sys; os.environ['DOCFIT_MCP_ENABLED']='1'; "
            "runpy.run_path(sys.argv[1], run_name='__main__')"
        )
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-c", launcher, str(server_script)],
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
