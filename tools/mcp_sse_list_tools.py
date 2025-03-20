import asyncio
import json
import logging
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.model.message import PromptMessageTool
from dify_plugin.entities.tool import ToolInvokeMessage
from mcp import types

from utils.mcp_sse_util import McpSseClient


class McpSseTool(Tool):

    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        servers_config_json = self.runtime.credentials.get("servers_config", "")
        if not servers_config_json:
            raise ValueError("Please fill in the servers_config")
        try:
            servers_config = json.loads(servers_config_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"servers_config must be a valid JSON string: {e}")

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
            tools = asyncio.run(fetch_tools())
            tools_description = json.dumps(
                [to_prompt_tool(tool).model_dump(mode="json") for tool in tools]
            )
            yield self.create_text_message(f"MCP Server tools list: \n{tools_description}")
        except Exception as e:
            error_msg = f"Error fetching tools: {e}"
            logging.error(error_msg)
            yield self.create_text_message(error_msg)


def to_prompt_tool(tool: types.Tool) -> PromptMessageTool:
    """
    Tool to prompt message tool
    """
    return PromptMessageTool(
        name=tool.name,
        description=tool.description,
        parameters=tool.inputSchema,
    )
