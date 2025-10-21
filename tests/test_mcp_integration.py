"""
Test MCP Integration with ACE Framework
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from ace.mcp_client import MCPClient, MCPToolManager, MCPTool, MCPToolCall
from ace.models import ACEConfig


class TestMCPClient:
    """Test MCP Client functionality"""

    def test_mcp_tool_creation(self):
        """Test MCPTool dataclass creation"""
        tool = MCPTool(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object", "properties": {}},
            server_name="test_server"
        )
        assert tool.name == "test_tool"
        assert tool.server_name == "test_server"

    def test_mcp_tool_call_creation(self):
        """Test MCPToolCall dataclass creation"""
        tool_call = MCPToolCall(
            tool_name="test_tool",
            arguments={"param": "value"},
            result="success",
            success=True
        )
        assert tool_call.tool_name == "test_tool"
        assert tool_call.success == True
        assert tool_call.result == "success"

    @pytest.mark.asyncio
    async def test_mcp_client_connection(self):
        """Test MCP client connection"""
        client = MCPClient("test_server", {"type": "stdio"})
        result = await client.connect()
        assert result is True
        assert client._connection is not None
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_mcp_client_list_tools(self):
        """Test MCP client tool listing"""
        client = MCPClient("filesystem", {"type": "stdio"})
        await client.connect()
        tools = await client.list_tools()
        assert len(tools) > 0
        assert all(isinstance(tool, MCPTool) for tool in tools)
        await client.disconnect()

    @pytest.mark.asyncio
    async def test_mcp_client_call_tool(self):
        """Test MCP client tool calling"""
        client = MCPClient("filesystem", {"type": "stdio"})
        await client.connect()

        # Test file write
        result = await client.call_tool("write_file", {
            "path": "test.txt",
            "content": "test content"
        })
        assert isinstance(result, MCPToolCall)
        assert result.tool_name == "write_file"

        await client.disconnect()


class TestMCPToolManager:
    """Test MCP Tool Manager functionality"""

    def setup_method(self):
        """Setup test configuration"""
        self.config = Mock(spec=ACEConfig)
        self.config.mcp_config = {
            'enabled': True,
            'servers': {
                'filesystem': {
                    'enabled': True,
                    'connection': {'type': 'stdio'}
                },
                'code_execution': {
                    'enabled': True,
                    'connection': {'type': 'stdio'}
                }
            }
        }

    @pytest.mark.asyncio
    async def test_mcp_manager_initialization(self):
        """Test MCP manager initialization"""
        manager = MCPToolManager(self.config)
        assert manager.enabled is True
        assert len(manager.servers) == 2

    @pytest.mark.asyncio
    async def test_mcp_manager_initialize(self):
        """Test MCP manager connection initialization"""
        manager = MCPToolManager(self.config)
        result = await manager.initialize()
        assert result is True
        assert manager._initialized is True
        assert len(manager.tools) > 0
        await manager.cleanup()

    def test_mcp_manager_disabled(self):
        """Test MCP manager when disabled"""
        self.config.mcp_config['enabled'] = False
        manager = MCPToolManager(self.config)
        assert manager.enabled is False
        assert len(manager.servers) == 0

    @pytest.mark.asyncio
    async def test_get_available_tools(self):
        """Test getting available tools"""
        manager = MCPToolManager(self.config)
        await manager.initialize()

        tools = manager.get_available_tools()
        assert len(tools) > 0
        assert all(isinstance(tool, MCPTool) for tool in tools)

        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_tools_description_for_llm(self):
        """Test tools description formatting for LLM"""
        manager = MCPToolManager(self.config)
        await manager.initialize()

        description = manager.get_tools_description_for_llm()
        assert isinstance(description, str)
        assert "Available MCP Tools" in description
        assert len(description) > 0

        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_call_tool_success(self):
        """Test successful tool call"""
        manager = MCPToolManager(self.config)
        await manager.initialize()

        # Find a valid tool
        tools = manager.get_available_tools()
        if tools:
            tool_key = f"{tools[0].server_name}.{tools[0].name}"
            result = await manager.call_tool(tool_key, {})

            assert isinstance(result, MCPToolCall)
            assert result.tool_name == tool_key

        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_call_tool_not_found(self):
        """Test calling non-existent tool"""
        manager = MCPToolManager(self.config)
        await manager.initialize()

        result = await manager.call_tool("nonexistent.tool", {})
        assert result.success is False
        assert "not found" in result.error

        await manager.cleanup()

    @pytest.mark.asyncio
    async def test_execute_tool_plan(self):
        """Test executing a sequence of tool calls"""
        manager = MCPToolManager(self.config)
        await manager.initialize()

        # Get available tools
        tools = manager.get_available_tools()
        if tools:
            tool_key = f"{tools[0].server_name}.{tools[0].name}"

            # Create a simple plan
            plan = [
                {"tool": tool_key, "arguments": {}}
            ]

            results = await manager.execute_tool_plan(plan)
            assert len(results) == 1
            assert isinstance(results[0], MCPToolCall)

        await manager.cleanup()


class TestMCPIntegrationWithGenerator:
    """Test MCP integration with Generator component"""

    def setup_method(self):
        """Setup test configuration"""
        self.config = Mock(spec=ACEConfig)
        self.config.mcp_config = {
            'enabled': True,
            'servers': {
                'filesystem': {
                    'enabled': True,
                    'connection': {'type': 'stdio'}
                }
            }
        }
        self.config.generator_model = "test-model"
        self.config.max_retrieved_bullets = 10
        self.config.min_bullet_helpfulness = 0

    @pytest.mark.asyncio
    async def test_generator_with_mcp_enabled(self):
        """Test Generator with MCP tools enabled"""
        from ace.generator import Generator
        from ace.llm_client import LLMClient
        from ace.models import Playbook

        # Mock LLM client
        llm_client = Mock(spec=LLMClient)
        llm_client.generate_json_response = AsyncMock(return_value={
            "reasoning_steps": ["Step 1: Use file system tool"],
            "generated_code": "# Generated code",
            "tool_calls": [
                {
                    "tool": "filesystem.read_file",
                    "arguments": {"path": "test.txt"}
                }
            ],
            "confidence": 0.8,
            "used_strategies": ["file_operations"]
        })

        # Create generator
        generator = Generator(self.config, llm_client)

        # Mock playbook
        playbook = Mock(spec=Playbook)
        playbook.get_relevant_bullets = Mock(return_value=[])

        # Generate trajectory with tools enabled
        trajectory = await generator.generate_trajectory(
            "Test query",
            playbook,
            enable_tools=True
        )

        assert trajectory.metadata.get("tools_enabled") is True
        assert "tool_calls" in trajectory.metadata

    @pytest.mark.asyncio
    async def test_generator_with_mcp_disabled(self):
        """Test Generator with MCP tools disabled"""
        from ace.generator import Generator
        from ace.llm_client import LLMClient
        from ace.models import Playbook

        # Mock LLM client
        llm_client = Mock(spec=LLMClient)
        llm_client.generate_json_response = AsyncMock(return_value={
            "reasoning_steps": ["Step 1: Solve without tools"],
            "generated_code": "# Generated code",
            "confidence": 0.7,
            "used_strategies": ["direct_solution"]
        })

        # Create generator with disabled MCP
        self.config.mcp_config['enabled'] = False
        generator = Generator(self.config, llm_client)

        # Mock playbook
        playbook = Mock(spec=Playbook)
        playbook.get_relevant_bullets = Mock(return_value=[])

        # Generate trajectory with tools disabled
        trajectory = await generator.generate_trajectory(
            "Test query",
            playbook,
            enable_tools=True  # Even if enabled=True, config should disable it
        )

        assert trajectory.metadata.get("tools_enabled") is False
        assert len(trajectory.metadata.get("tool_calls", [])) == 0


class TestMCPConfiguration:
    """Test MCP configuration loading"""

    def test_mcp_config_loading(self):
        """Test loading MCP configuration from config file"""
        from ace.config_loader import get_ace_config

        # This will load from the actual config.yaml file
        config = get_ace_config()

        # Check if MCP config exists
        assert hasattr(config, 'mcp_config')

        mcp_config = config.mcp_config
        assert 'enabled' in mcp_config
        assert 'servers' in mcp_config

        if mcp_config['enabled']:
            assert len(mcp_config['servers']) > 0
            for server_name, server_config in mcp_config['servers'].items():
                assert 'enabled' in server_config
                assert 'connection' in server_config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])