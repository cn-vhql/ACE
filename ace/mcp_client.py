"""
MCP Client and Tool Management for ACE Framework
Integration point for Model Context Protocol tools
"""
import asyncio
import json
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import logging
from .models import ACEConfig

logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    """Represents an available MCP tool"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str


@dataclass
class MCPToolCall:
    """Represents a tool call execution"""
    tool_name: str
    arguments: Dict[str, Any]
    result: Any
    success: bool
    error: Optional[str] = None


class MCPClient:
    """Client for connecting to MCP servers"""

    def __init__(self, server_name: str, connection_params: Dict[str, Any]):
        self.server_name = server_name
        self.connection_params = connection_params
        self._connection = None
        self._tools_cache: Optional[List[MCPTool]] = None

    async def connect(self) -> bool:
        """Connect to MCP server"""
        try:
            # For now, we'll simulate MCP connection
            # In real implementation, this would establish actual MCP protocol connection
            logger.info(f"Connecting to MCP server: {self.server_name}")
            self._connection = f"connected_to_{self.server_name}"
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {self.server_name}: {e}")
            return False

    async def disconnect(self):
        """Disconnect from MCP server"""
        if self._connection:
            logger.info(f"Disconnecting from MCP server: {self.server_name}")
            self._connection = None

    async def list_tools(self) -> List[MCPTool]:
        """List available tools from this server"""
        if not self._connection:
            await self.connect()

        if self._tools_cache:
            return self._tools_cache

        # Simulate tool discovery
        # In real implementation, this would use MCP protocol to list tools
        mock_tools = self._get_mock_tools()
        self._tools_cache = mock_tools
        return mock_tools

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPToolCall:
        """Execute a tool call"""
        if not self._connection:
            await self.connect()

        try:
            # Simulate tool execution
            # In real implementation, this would use MCP protocol
            result = await self._simulate_tool_execution(tool_name, arguments)
            return MCPToolCall(
                tool_name=tool_name,
                arguments=arguments,
                result=result,
                success=True
            )
        except Exception as e:
            logger.error(f"Tool call failed: {tool_name}: {e}")
            return MCPToolCall(
                tool_name=tool_name,
                arguments=arguments,
                result=None,
                success=False,
                error=str(e)
            )

    def _get_mock_tools(self) -> List[MCPTool]:
        """Get mock tools for demonstration"""
        if self.server_name == "filesystem":
            return [
                MCPTool(
                    name="read_file",
                    description="Read contents of a file",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path to read"}
                        },
                        "required": ["path"]
                    },
                    server_name=self.server_name
                ),
                MCPTool(
                    name="write_file",
                    description="Write content to a file",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path to write"},
                            "content": {"type": "string", "description": "Content to write"}
                        },
                        "required": ["path", "content"]
                    },
                    server_name=self.server_name
                ),
                MCPTool(
                    name="list_directory",
                    description="List contents of a directory",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Directory path to list"}
                        },
                        "required": ["path"]
                    },
                    server_name=self.server_name
                )
            ]
        elif self.server_name == "code_execution":
            return [
                MCPTool(
                    name="execute_code",
                    description="Execute code in a sandboxed environment",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Code to execute"},
                            "language": {"type": "string", "description": "Programming language"}
                        },
                        "required": ["code"]
                    },
                    server_name=self.server_name
                )
            ]
        elif self.server_name == "web_search":
            return [
                MCPTool(
                    name="search_web",
                    description="Search the web for information",
                    input_schema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"},
                            "max_results": {"type": "integer", "description": "Maximum number of results"}
                        },
                        "required": ["query"]
                    },
                    server_name=self.server_name
                )
            ]
        return []

    async def _simulate_tool_execution(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Simulate tool execution for demonstration"""
        await asyncio.sleep(0.1)  # Simulate network delay

        if self.server_name == "filesystem":
            if tool_name == "read_file":
                path = arguments.get("path", "")
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        return {"content": f.read(), "success": True}
                except Exception as e:
                    return {"error": str(e), "success": False}

            elif tool_name == "write_file":
                path = arguments.get("path", "")
                content = arguments.get("content", "")
                try:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    return {"success": True, "message": f"Written to {path}"}
                except Exception as e:
                    return {"error": str(e), "success": False}

            elif tool_name == "list_directory":
                import os
                path = arguments.get("path", "")
                try:
                    items = os.listdir(path)
                    return {"items": items, "success": True}
                except Exception as e:
                    return {"error": str(e), "success": False}

        elif self.server_name == "code_execution":
            if tool_name == "execute_code":
                code = arguments.get("code", "")
                language = arguments.get("language", "python")

                if language == "python":
                    try:
                        # Create a namespace for execution
                        namespace = {}
                        exec(code, namespace)

                        # Extract variables from namespace
                        result_vars = {}
                        for name, value in namespace.items():
                            if not name.startswith("__"):
                                try:
                                    # Try to serialize the value to ensure it's JSON-serializable
                                    json.dumps(value)
                                    result_vars[name] = str(value)[:1000]  # Limit output size
                                except:
                                    result_vars[name] = f"<{type(value).__name__} object>"

                        return {
                            "output": result_vars,
                            "success": True,
                            "language": language
                        }
                    except Exception as e:
                        return {"error": str(e), "success": False, "language": language}
                else:
                    return {"error": f"Language {language} not supported in simulation", "success": False}

        elif self.server_name == "web_search":
            if tool_name == "search_web":
                query = arguments.get("query", "")
                max_results = arguments.get("max_results", 5)

                # Simulate web search results
                return {
                    "results": [
                        {
                            "title": f"Search result for '{query}' - {i+1}",
                            "url": f"https://example.com/result{i+1}",
                            "snippet": f"This is a mock search result snippet for query: {query}"
                        }
                        for i in range(min(max_results, 3))
                    ],
                    "query": query,
                    "success": True
                }

        return {"error": f"Unknown tool: {tool_name}", "success": False}


class MCPToolManager:
    """Manages multiple MCP servers and tool execution"""

    def __init__(self, config: ACEConfig):
        self.config = config
        self.servers: Dict[str, MCPClient] = {}
        self.tools: Dict[str, MCPTool] = {}
        self._initialized = False

        # Load MCP configuration
        self.mcp_config = getattr(config, 'mcp_config', {})
        self.enabled = self.mcp_config.get('enabled', False)

        if self.enabled:
            self._initialize_servers()

    def _initialize_servers(self):
        """Initialize MCP servers from configuration"""
        servers_config = self.mcp_config.get('servers', {})

        for server_name, server_config in servers_config.items():
            if server_config.get('enabled', True):
                client = MCPClient(server_name, server_config)
                self.servers[server_name] = client
                logger.info(f"Initialized MCP server client: {server_name}")

    async def initialize(self) -> bool:
        """Initialize all MCP connections and discover tools"""
        if not self.enabled:
            logger.info("MCP tools are disabled in configuration")
            return False

        if self._initialized:
            return True

        logger.info("Initializing MCP Tool Manager...")

        # Connect to all servers and discover tools
        for server_name, client in self.servers.items():
            try:
                if await client.connect():
                    tools = await client.list_tools()
                    for tool in tools:
                        # Create a unique tool name
                        tool_key = f"{server_name}.{tool.name}"
                        self.tools[tool_key] = tool
                    logger.info(f"Connected to {server_name}, discovered {len(tools)} tools")
                else:
                    logger.warning(f"Failed to connect to MCP server: {server_name}")
            except Exception as e:
                logger.error(f"Error initializing MCP server {server_name}: {e}")

        self._initialized = True
        logger.info(f"MCP Tool Manager initialized with {len(self.tools)} tools")
        return True

    async def cleanup(self):
        """Cleanup MCP connections"""
        for client in self.servers.values():
            await client.disconnect()
        self.servers.clear()
        self.tools.clear()
        self._initialized = False

    def get_available_tools(self) -> List[MCPTool]:
        """Get list of all available tools"""
        return list(self.tools.values())

    def get_tools_description_for_llm(self) -> str:
        """Get formatted description of tools for LLM consumption"""
        if not self.tools:
            return "No MCP tools available."

        description = "Available MCP Tools:\n"
        description += "=" * 40 + "\n"

        for tool_key, tool in self.tools.items():
            description += f"\n{tool_key}:\n"
            description += f"  Description: {tool.description}\n"
            description += f"  Server: {tool.server_name}\n"

            # Format input schema
            if "properties" in tool.input_schema:
                description += "  Parameters:\n"
                for param_name, param_info in tool.input_schema["properties"].items():
                    param_type = param_info.get("type", "unknown")
                    param_desc = param_info.get("description", "")
                    required = param_name in tool.input_schema.get("required", [])
                    req_marker = " (required)" if required else " (optional)"
                    description += f"    - {param_name}: {param_type}{req_marker} - {param_desc}\n"

        description += "=" * 40 + "\n"
        return description

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPToolCall:
        """Execute a tool call"""
        if tool_name not in self.tools:
            return MCPToolCall(
                tool_name=tool_name,
                arguments=arguments,
                result=None,
                success=False,
                error=f"Tool '{tool_name}' not found. Available tools: {list(self.tools.keys())}"
            )

        tool = self.tools[tool_name]
        server_name = tool.server_name

        if server_name not in self.servers:
            return MCPToolCall(
                tool_name=tool_name,
                arguments=arguments,
                result=None,
                success=False,
                error=f"Server '{server_name}' not available for tool '{tool_name}'"
            )

        client = self.servers[server_name]
        return await client.call_tool(tool.name, arguments)

    async def execute_tool_plan(self, tool_plan: List[Dict[str, Any]]) -> List[MCPToolCall]:
        """Execute a sequence of tool calls"""
        results = []

        for step in tool_plan:
            tool_name = step.get("tool")
            arguments = step.get("arguments", {})

            if not tool_name:
                results.append(MCPToolCall(
                    tool_name="unknown",
                    arguments=arguments,
                    result=None,
                    success=False,
                    error="No tool name specified in step"
                ))
                continue

            result = await self.call_tool(tool_name, arguments)
            results.append(result)

            # Stop execution if a critical step fails
            if not result.success and step.get("required", True):
                logger.error(f"Required tool step failed: {tool_name}: {result.error}")
                break

        return results