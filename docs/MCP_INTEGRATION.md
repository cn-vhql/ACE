# MCP Integration for ACE Framework

This document describes the integration of Model Context Protocol (MCP) tools with the ACE framework, enabling the Generator component to use external tools for enhanced problem-solving capabilities.

## Overview

MCP (Model Context Protocol) allows language models to interact with external tools and services, significantly expanding their capabilities beyond text generation. By integrating MCP with ACE, the Generator component can:

- **File System Operations**: Read, write, and manipulate files
- **Code Execution**: Run code in sandboxed environments
- **Web Access**: Search the web and access online resources
- **Database Operations**: Query and manage databases
- **Git Operations**: Version control and repository management
- **Custom Tools**: Any tool that supports the MCP protocol

## Architecture

### Components

1. **MCPClient** (`ace/mcp_client.py`): Handles communication with individual MCP servers
2. **MCPToolManager** (`ace/mcp_client.py`): Manages multiple MCP servers and tool orchestration
3. **Generator Enhancement** (`ace/generator.py`): Extended to support MCP tool calls
4. **Configuration System** (`config.yaml`): MCP server configurations and settings

### Data Flow

```
Query → Generator → LLM (with tool descriptions) → Tool Calls → MCP Manager → MCP Servers → Results → Generator
```

## Configuration

### Basic Setup

In your `config.yaml`, add the MCP configuration:

```yaml
mcp:
  enabled: true

  servers:
    filesystem:
      enabled: true
      connection:
        type: "stdio"
        command: "npx"
        args: ["@modelcontextprotocol/server-filesystem", "/tmp"]
      timeout: 30

    code_execution:
      enabled: true
      connection:
        type: "stdio"
        command: "npx"
        args: ["@modelcontextprotocol/server-executor"]
      timeout: 60

    web_search:
      enabled: true
      connection:
        type: "stdio"
        command: "npx"
        args: ["@modelcontextprotocol/server-web-search"]
      timeout: 30
```

### Server Configuration Options

Each MCP server can be configured with:

- `enabled`: Whether this server is active
- `connection`: Connection parameters (type, command, args)
- `timeout`: Request timeout in seconds
- `custom_params`: Server-specific parameters

### Global Settings

```yaml
mcp:
  settings:
    max_concurrent_calls: 5
    default_timeout: 30
    cache_results: true
    cache_duration: 300
```

## Usage

### Basic Usage

```python
from ace import ACE
from ace.config_loader import get_ace_config

config = get_ace_config()
ace = ACE(config)

# Enable MCP tools in query solving
trajectory, reflection = await ace.solve_query(
    "Create a file with analysis results",
    enable_tools=True
)
```

### Advanced Usage

```python
# Custom tool usage
from ace.generator import Generator
from ace.llm_client import LLMClient

generator = Generator(config, llm_client)

# Generate trajectory with explicit tool control
trajectory = await generator.generate_trajectory(
    query="Analyze data and save results",
    playbook=playbook,
    enable_tools=True
)

# Check tool calls made
tool_calls = trajectory.metadata.get("tool_calls", [])
for tool_call in tool_calls:
    print(f"Tool: {tool_call['tool_name']}")
    print(f"Success: {tool_call['success']}")
    if tool_call['result']:
        print(f"Result: {tool_call['result']}")
```

### Direct MCP Usage

```python
from ace.mcp_client import MCPToolManager

manager = MCPToolManager(config)
await manager.initialize()

# Call specific tool
result = await manager.call_tool(
    'filesystem.write_file',
    {'path': 'output.txt', 'content': 'Hello from MCP!'}
)

# Execute multiple tools in sequence
plan = [
    {'tool': 'filesystem.read_file', 'arguments': {'path': 'input.txt'}},
    {'tool': 'code_execution.execute_code', 'arguments': {'code': 'print("processing...")'}},
    {'tool': 'filesystem.write_file', 'arguments': {'path': 'output.txt', 'content': 'processed'}}
]

results = await manager.execute_tool_plan(plan)
```

## Available Tools

### File System Tools

- `filesystem.read_file`: Read file contents
- `filesystem.write_file`: Write content to files
- `filesystem.list_directory`: List directory contents
- `filesystem.create_directory`: Create directories
- `filesystem.delete_file`: Delete files

### Code Execution Tools

- `code_execution.execute_code`: Execute code in various languages
- `code_execution.run_command`: Execute shell commands
- `code_execution.install_package`: Install packages

### Web Search Tools

- `web_search.search_web`: Search the web
- `web_search.fetch_url`: Fetch web page content
- `web_search.get_page_info`: Extract page metadata

### Database Tools

- `database.execute_query`: Execute SQL queries
- `database.get_schema`: Get database schema
- `database.insert_data`: Insert data into tables

### Git Tools

- `git.clone_repository`: Clone git repositories
- `git.commit_changes`: Commit changes
- `git.push_changes`: Push to remote
- `git.create_branch`: Create branches

## Error Handling

### Tool Call Failures

When a tool call fails, the system:

1. Logs the error with detailed information
2. Continues with subsequent tool calls if they're not required
3. Includes error information in the trajectory metadata
4. Allows the LLM to adapt and try alternative approaches

### Connection Issues

The MCP Manager handles connection issues gracefully:

- Automatic reconnection attempts
- Fallback to tools without external dependencies
- Detailed error reporting for debugging

## Performance Considerations

### Concurrent Tool Calls

```yaml
mcp:
  settings:
    max_concurrent_calls: 5  # Execute up to 5 tools in parallel
```

### Caching

Tool results can be cached to avoid redundant operations:

```yaml
mcp:
  settings:
    cache_results: true
    cache_duration: 300  # Cache for 5 minutes
```

### Timeouts

Configure appropriate timeouts for different tool types:

```yaml
mcp:
  servers:
    code_execution:
      timeout: 120  # Longer timeout for complex computations
    web_search:
      timeout: 30   # Shorter timeout for network operations
```

## Security Considerations

### File System Access

- Limit file system access to specific directories
- Use sandboxed environments for code execution
- Implement access controls for sensitive operations

### Code Execution

- Run code in isolated containers or sandboxes
- Limit resource usage (CPU, memory, time)
- Monitor for malicious code patterns

### Network Access

- Restrict access to approved domains
- Implement rate limiting for web searches
- Sanitize inputs and outputs

## Troubleshooting

### Common Issues

1. **MCP Server Not Starting**
   - Check if Node.js and npm are installed
   - Verify server package installation: `npm install -g @modelcontextprotocol/server-*`
   - Check connection parameters in config

2. **Tool Calls Failing**
   - Verify tool arguments match expected schema
   - Check server logs for error details
   - Ensure sufficient permissions for operations

3. **Performance Issues**
   - Reduce `max_concurrent_calls` if system is overloaded
   - Increase timeouts for slow operations
   - Enable caching for frequently used operations

### Debug Mode

Enable debug logging to troubleshoot issues:

```yaml
logging:
  level: "DEBUG"
```

This will show detailed MCP communication logs.

## Examples

### Example 1: File Processing Pipeline

```python
query = """
Read data from 'input.csv', process it with Python,
and save results to 'output.txt'
"""

trajectory, reflection = await ace.solve_query(query, enable_tools=True)
```

### Example 2: Web Research and Report

```python
query = """
Research latest AI trends, summarize findings,
and save a report to 'ai_trends_report.txt'
"""

trajectory, reflection = await ace.solve_query(query, enable_tools=True)
```

### Example 3: Code Analysis and Refactoring

```python
query = """
Analyze the Python files in this project,
identify code quality issues, and create
refactoring suggestions in a file called 'refactor_plan.md'
"""

trajectory, reflection = await ace.solve_query(query, enable_tools=True)
```

## Integration with Existing ACE Features

### Playbook Integration

MCP tool usage is automatically incorporated into the playbook evolution process:

- Successful tool patterns are recorded as new bullets
- Failed tool attempts generate learning insights
- Tool strategies are refined over time

### Reflection Enhancement

The Reflector component analyzes:

- Tool selection effectiveness
- Tool usage patterns
- Error handling strategies
- Optimization opportunities

### Performance Metrics

Track MCP integration performance:

```python
stats = ace.get_statistics()
mcp_stats = stats.get('mcp_integration', {})

print(f"Tool calls made: {mcp_stats.get('total_tool_calls', 0)}")
print(f"Tool success rate: {mcp_stats.get('success_rate', 0):.1%}")
print(f"Most used tools: {mcp_stats.get('most_used_tools', [])}")
```

## Future Enhancements

### Planned Features

1. **Custom Tool Development**: Framework for creating custom MCP tools
2. **Tool Composition**: Support for complex tool workflows
3. **Dynamic Tool Loading**: Runtime tool discovery and loading
4. **Tool Marketplace**: Integration with external tool repositories
5. **Performance Analytics**: Advanced tool usage analytics and optimization

### Extension Points

- Custom MCP server implementations
- Tool-specific caching strategies
- Advanced error handling patterns
- Tool usage policy enforcement

## References

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [MCP Server Documentation](https://github.com/modelcontextprotocol/servers)
- [ACE Framework Documentation](../README.md)