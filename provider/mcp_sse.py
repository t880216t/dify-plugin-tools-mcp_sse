import asyncio
import json
import logging
from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from utils.mcp_sse_util import McpSseClient


class McpSseProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        servers_config_json = credentials.get("servers_config", "")
        if not servers_config_json:
            raise ToolProviderCredentialValidationError("Please fill in the servers_config")
        try:
            servers_config = json.loads(servers_config_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"servers_config must be a valid JSON string: {e}")
        print(servers_config)
        clients = [
            McpSseClient(name, config) for name, config in servers_config.items()
        ]

        async def fetch_tools():
            all_tools = []
            for client in clients:
                try:
                    await client.initialize()
                    tools = await client.list_tools()
                finally:
                    await client.cleanup()
                all_tools.extend(tools)
            return all_tools

        try:
            asyncio.run(fetch_tools())
        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e))
