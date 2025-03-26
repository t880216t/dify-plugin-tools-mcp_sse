import json
from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from utils.mcp_client import McpClientsUtil


class McpSseProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        servers_config_json = credentials.get("servers_config", "")
        if not servers_config_json:
            raise ToolProviderCredentialValidationError("Please fill in the servers_config")
        try:
            servers_config = json.loads(servers_config_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"servers_config must be a valid JSON string: {e}")

        try:
            McpClientsUtil.fetch_tools(servers_config)
        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e))
