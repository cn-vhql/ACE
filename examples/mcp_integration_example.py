"""
MCP Integration Example for ACE Framework
Demonstrates how to use MCP tools in the Generator component
"""
import asyncio
import logging
from ace import ACE
from ace.config_loader import get_ace_config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demonstrate_mcp_integration():
    """Demonstrate MCP tools integration in ACE framework"""
    print("🚀 ACE Framework MCP Integration Example")
    print("=" * 50)

    # Load configuration
    config = get_ace_config()
    ace = ACE(config)

    # Example 1: File operations with MCP tools
    print("\n📁 Example 1: File Operations with MCP Tools")
    print("-" * 40)

    file_query = """
    Create a Python script that reads a configuration file, processes the data,
    and writes the results to a new file. The script should:
    1. Read from 'config.json'
    2. Process the configuration data
    3. Write processed results to 'output.txt'
    """

    trajectory, reflection = await ace.solve_query(file_query, enable_tools=True)

    print(f"Query: {file_query}")
    print(f"Success: {trajectory.success}")
    print(f"Reasoning Steps: {len(trajectory.reasoning_steps)}")

    # Show tool calls if any were made
    tool_calls = trajectory.metadata.get("tool_calls", [])
    if tool_calls:
        print(f"Tool Calls Made: {len(tool_calls)}")
        for i, tool_call in enumerate(tool_calls, 1):
            print(f"  {i}. {tool_call['tool_name']}: {tool_call['success']}")
    else:
        print("No tool calls were made")

    # Example 2: Web search and analysis
    print("\n🌐 Example 2: Web Search and Analysis")
    print("-" * 40)

    search_query = """
    Research the latest trends in artificial intelligence and machine learning.
    Use web search to find current information, then create a summary report
    and save it to a file named 'ai_trends_report.txt'.
    """

    trajectory, reflection = await ace.solve_query(search_query, enable_tools=True)

    print(f"Query: {search_query}")
    print(f"Success: {trajectory.success}")
    print(f"Reasoning Steps: {len(trajectory.reasoning_steps)}")

    # Show tool calls if any were made
    tool_calls = trajectory.metadata.get("tool_calls", [])
    if tool_calls:
        print(f"Tool Calls Made: {len(tool_calls)}")
        for i, tool_call in enumerate(tool_calls, 1):
            print(f"  {i}. {tool_call['tool_name']}: {tool_call['success']}")

    # Example 3: Code execution with multiple tools
    print("\n⚙️ Example 3: Advanced Code Execution with Multiple Tools")
    print("-" * 40)

    advanced_query = """
    Create a data analysis pipeline that:
    1. Reads a CSV file from the file system
    2. Performs statistical analysis using Python
    3. Generates visualizations
    4. Saves the results to a new file

    First check what files are available in the current directory,
    then create a sample CSV file if needed, and perform the analysis.
    """

    trajectory, reflection = await ace.solve_query(advanced_query, enable_tools=True)

    print(f"Query: {advanced_query}")
    print(f"Success: {trajectory.success}")
    print(f"Reasoning Steps: {len(trajectory.reasoning_steps)}")

    # Show detailed tool call information
    tool_calls = trajectory.metadata.get("tool_calls", [])
    if tool_calls:
        print(f"Tool Calls Made: {len(tool_calls)}")
        for i, tool_call in enumerate(tool_calls, 1):
            status = "✅" if tool_call['success'] else "❌"
            print(f"  {i}. {status} {tool_call['tool_name']}")
            if tool_call['error']:
                print(f"     Error: {tool_call['error']}")

    # Show the generated code
    if trajectory.generated_code:
        print(f"\nGenerated Code Preview:")
        print("-" * 20)
        print(trajectory.generated_code[:500] + "..." if len(trajectory.generated_code) > 500 else trajectory.generated_code)

    # Example 4: Compare with and without MCP tools
    print("\n📊 Example 4: Comparison: With vs Without MCP Tools")
    print("-" * 50)

    comparison_query = "Create a simple 'hello.txt' file with a greeting message."

    print("Without MCP Tools:")
    trajectory_without = await ace.solve_query(comparison_query, enable_tools=False)
    print(f"  Success: {trajectory_without.success}")
    print(f"  Tool Calls: {len(trajectory_without.metadata.get('tool_calls', []))}")

    print("\nWith MCP Tools:")
    trajectory_with = await ace.solve_query(comparison_query, enable_tools=True)
    print(f"  Success: {trajectory_with.success}")
    print(f"  Tool Calls: {len(trajectory_with.metadata.get('tool_calls', []))}")

    # Show statistics
    print("\n📈 MCP Integration Statistics")
    print("-" * 30)

    # Get playbook summary
    playbook_summary = ace.get_playbook_summary()
    stats = ace.get_statistics()

    print(f"Playbook Bullets: {playbook_summary['total_bullets']}")
    print(f"Total Queries Processed: {stats.get('total_queries', 0)}")
    print(f"Success Rate: {stats.get('success_rate', 0):.1%}")

    # Cleanup MCP connections
    if hasattr(ace.generator, 'mcp_manager'):
        await ace.generator.mcp_manager.cleanup()
        print("\n🧹 MCP connections cleaned up")

    print("\n✅ MCP Integration Example Complete!")


async def test_mcp_tools_directly():
    """Test MCP tools directly without going through ACE"""
    print("\n🔧 Testing MCP Tools Directly")
    print("=" * 30)

    from ace.mcp_client import MCPToolManager
    from ace.config_loader import get_ace_config

    config = get_ace_config()
    mcp_manager = MCPToolManager(config)

    # Initialize MCP manager
    if await mcp_manager.initialize():
        print("✅ MCP Manager initialized successfully")

        # Get available tools
        tools = mcp_manager.get_available_tools()
        print(f"📋 Available Tools: {len(tools)}")

        for tool in tools:
            print(f"  - {tool.server_name}.{tool.name}: {tool.description}")

        # Test file system tools
        if 'filesystem.read_file' in [f"{t.server_name}.{t.name}" for t in tools]:
            print("\n📁 Testing file system tools...")

            # Write a test file
            write_result = await mcp_manager.call_tool(
                'filesystem.write_file',
                {'path': 'test_mcp.txt', 'content': 'Hello from MCP!'}
            )
            print(f"Write result: {write_result.success}")

            # Read the test file
            read_result = await mcp_manager.call_tool(
                'filesystem.read_file',
                {'path': 'test_mcp.txt'}
            )
            print(f"Read result: {read_result.success}")
            if read_result.success:
                print(f"Content: {read_result.result.get('content', '')[:50]}...")

        # Test code execution tools
        if 'code_execution.execute_code' in [f"{t.server_name}.{t.name}" for t in tools]:
            print("\n⚙️ Testing code execution tools...")

            code_result = await mcp_manager.call_tool(
                'code_execution.execute_code',
                {'code': 'print("Hello from MCP code execution!")', 'language': 'python'}
            )
            print(f"Code execution result: {code_result.success}")
            if code_result.success:
                print(f"Output: {code_result.result}")

        # Test web search tools
        if 'web_search.search_web' in [f"{t.server_name}.{t.name}" for t in tools]:
            print("\n🌐 Testing web search tools...")

            search_result = await mcp_manager.call_tool(
                'web_search.search_web',
                {'query': 'MCP Model Context Protocol', 'max_results': 3}
            )
            print(f"Web search result: {search_result.success}")
            if search_result.success:
                results = search_result.result.get('results', [])
                print(f"Found {len(results)} results")

        # Cleanup
        await mcp_manager.cleanup()
        print("\n🧹 MCP Manager cleaned up")
    else:
        print("❌ Failed to initialize MCP Manager")


async def main():
    """Main function to run all examples"""
    try:
        # Run the main demonstration
        await demonstrate_mcp_integration()

        # Test MCP tools directly
        await test_mcp_tools_directly()

    except KeyboardInterrupt:
        print("\n⚠️ Example interrupted by user")
    except Exception as e:
        print(f"\n❌ Error running example: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())