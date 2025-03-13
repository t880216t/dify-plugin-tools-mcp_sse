import asyncio
import json
import logging
from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

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

        tool_name = tool_parameters.get("tool_name", "")
        if not tool_name:
            raise ValueError("Please fill in the tool_name")
        arguments_json = tool_parameters.get("arguments", "")
        if not arguments_json:
            raise ValueError("Please fill in the arguments")
        try:
            arguments = json.loads(arguments_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Arguments must be a valid JSON string: {e}")

        clients = [
            McpSseClient(name, config) for name, config in servers_config.items()
        ]

        async def execute_tool():
            for client in clients:
                try:
                    await client.initialize()
                    tools = await client.list_tools()
                except Exception as e:
                    error_msg = f"Error initializing or list tools: {str(e)}"
                    logging.error(error_msg)
                    continue
                finally:
                    await client.cleanup()
                if any(tool.name == tool_name for tool in tools):
                    try:
                        result = await client.execute_tool(tool_name, arguments)
                        if isinstance(result, dict) and "progress" in result:
                            progress = result["progress"]
                            total = result["total"]
                            percentage = (progress / total) * 100
                            logging.info(
                                f"Progress: {progress}/{total} "
                                f"({percentage:.1f}%)"
                            )
                        return f"Tool execution result: {result}"
                    except Exception as e:
                        error_msg = f"Error executing tool: {str(e)}"
                        logging.error(error_msg)
                        return error_msg
                    finally:
                        await client.cleanup()

        try:
            result = asyncio.run(execute_tool())
            yield self.create_text_message(result)
        except Exception as e:
            error_msg = f"Error executing tool: {str(e)}"
            logging.error(error_msg)
            yield self.create_text_message(error_msg)
