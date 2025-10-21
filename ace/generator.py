"""
Generator Component for ACE Framework
"""
from typing import List, Dict, Any, Optional
import json
import logging
from .models import Trajectory, Playbook, Bullet, ACEConfig
from .llm_client import LLMClient
from .mcp_client import MCPToolManager, MCPToolCall

logger = logging.getLogger(__name__)


class Generator:
    """Generates reasoning trajectories using the current playbook"""

    def __init__(self, config: ACEConfig, llm_client: LLMClient):
        self.config = config
        self.llm_client = llm_client
        self.mcp_manager = MCPToolManager(config)
        self._mcp_initialized = False
    
    async def generate_trajectory(
        self,
        query: str,
        playbook: Playbook,
        context: Optional[Dict[str, Any]] = None,
        enable_tools: bool = True
    ) -> Trajectory:
        """Generate a reasoning trajectory for the given query"""

        # Initialize MCP tools if enabled and not already initialized
        if enable_tools and not self._mcp_initialized:
            await self.mcp_manager.initialize()
            self._mcp_initialized = True

        # Retrieve relevant bullets from playbook
        relevant_bullets = playbook.get_relevant_bullets(
            query,
            max_bullets=self.config.max_retrieved_bullets
        )

        # Filter bullets by helpfulness
        filtered_bullets = [
            bullet for bullet in relevant_bullets
            if bullet.helpful_count >= self.config.min_bullet_helpfulness
        ]

        # Format playbook content
        playbook_content = self._format_playbook_for_generation(filtered_bullets)

        # Get available tools if MCP is enabled
        tools_description = ""
        if enable_tools and self.mcp_manager.enabled:
            tools_description = self.mcp_manager.get_tools_description_for_llm()

        # Generate trajectory
        trajectory = await self._generate_trajectory_with_llm(
            query, playbook_content, context, tools_description, enable_tools
        )

        # Track which bullets were used
        trajectory.used_bullet_ids = [bullet.id for bullet in filtered_bullets]

        return trajectory
    
    def _format_playbook_for_generation(self, bullets: List[Bullet]) -> str:
        """Format bullets for inclusion in the generation prompt"""
        if not bullets:
            return "No relevant strategies found in playbook."
        
        content = "ACE Playbook:\n"
        content += "=" * 50 + "\n"
        
        # Group bullets by section
        sections = {}
        for bullet in bullets:
            if bullet.section not in sections:
                sections[bullet.section] = []
            sections[bullet.section].append(bullet)
        
        for section, section_bullets in sections.items():
            content += f"\n{section.upper()}:\n"
            content += "-" * 20 + "\n"
            for bullet in section_bullets:
                tag = bullet.tag().value.upper()
                content += f"[{tag}] {bullet.content}\n"
        
        content += "=" * 50 + "\n"
        return content
    
    async def _generate_trajectory_with_llm(
        self,
        query: str,
        playbook_content: str,
        context: Optional[Dict[str, Any]],
        tools_description: str = "",
        enable_tools: bool = False
    ) -> Trajectory:
        """Generate trajectory using LLM with optional MCP tool support"""

        if enable_tools and tools_description:
            system_prompt = f"""You are an expert AI assistant that solves problems step-by-step.
You have access to a curated playbook of strategies and insights from previous experiences.
You also have access to external tools through MCP (Model Context Protocol) that can help you solve problems more effectively.

Your task is to:
1. Carefully analyze the problem and the playbook
2. Apply relevant strategies from the playbook
3. Use available tools when they can help solve the problem
4. Provide detailed reasoning steps
5. Generate code if needed
6. Explain your approach clearly

When using tools:
- Choose the most appropriate tool for the task
- Provide clear arguments to the tool calls
- Include tool results in your reasoning steps
- If a tool call fails, explain why and try an alternative approach

{tools_description}

Always structure your response as a JSON object with the following fields:
- reasoning_steps: List of reasoning steps (including tool usage)
- generated_code: Optional code solution
- tool_calls: List of tool calls made (each with tool, arguments, and result summary)
- confidence: Your confidence level (0-1)
- used_strategies: List of playbook strategies you used"""
        else:
            system_prompt = """You are an expert AI assistant that solves problems step-by-step.
You have access to a curated playbook of strategies and insights from previous experiences.
Your task is to:
1. Carefully analyze the problem and the playbook
2. Apply relevant strategies from the playbook
3. Provide detailed reasoning steps
4. Generate code if needed
5. Explain your approach clearly

Always structure your response as a JSON object with the following fields:
- reasoning_steps: List of reasoning steps
- generated_code: Optional code solution
- confidence: Your confidence level (0-1)
- used_strategies: List of playbook strategies you used"""

        prompt = f"""Problem: {query}

{playbook_content}"""

        if enable_tools and tools_description:
            prompt += f"""

Available Tools:
{tools_description}

If you need to use any tools, include them in your reasoning steps and tool_calls list."""

        prompt += f"""

Additional Context: {json.dumps(context, indent=2) if context else 'None'}

Please solve this problem using the playbook strategies, available tools, and your reasoning."""
        
        try:
            response = await self.llm_client.generate_json_response(
                prompt,
                model=self.config.generator_model,
                temperature=0.7,
                system_prompt=system_prompt
            )

            # Execute tool calls if any were requested
            tool_calls = response.get("tool_calls", [])
            executed_tool_calls = []

            if enable_tools and tool_calls:
                logger.info(f"Executing {len(tool_calls)} tool calls for query: {query}")
                executed_tool_calls = await self._execute_tool_calls(tool_calls)

            trajectory = Trajectory(
                query=query,
                reasoning_steps=response.get("reasoning_steps", []),
                generated_code=response.get("generated_code"),
                metadata={
                    "confidence": response.get("confidence", 0.5),
                    "used_strategies": response.get("used_strategies", []),
                    "tool_calls": [self._serialize_tool_call(tc) for tc in executed_tool_calls],
                    "tools_enabled": enable_tools,
                    "raw_response": response
                }
            )

            return trajectory
            
        except Exception as e:
            # Fallback to simple text response
            text_response = await self.llm_client.generate_response(
                prompt,
                model=self.config.generator_model,
                temperature=0.7,
                system_prompt="You are a helpful AI assistant. Provide step-by-step reasoning."
            )
            
            trajectory = Trajectory(
                query=query,
                reasoning_steps=[text_response],
                metadata={"error": str(e), "fallback": True, "tools_enabled": enable_tools}
            )

            return trajectory

    async def _execute_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[MCPToolCall]:
        """Execute a list of tool calls"""
        executed_calls = []

        for tool_call in tool_calls:
            tool_name = tool_call.get("tool")
            arguments = tool_call.get("arguments", {})

            if not tool_name:
                logger.warning("Tool call missing tool name")
                continue

            try:
                result = await self.mcp_manager.call_tool(tool_name, arguments)
                executed_calls.append(result)

                if result.success:
                    logger.info(f"Tool call succeeded: {tool_name}")
                else:
                    logger.warning(f"Tool call failed: {tool_name}: {result.error}")

            except Exception as e:
                logger.error(f"Error executing tool call {tool_name}: {e}")
                executed_calls.append(MCPToolCall(
                    tool_name=tool_name,
                    arguments=arguments,
                    result=None,
                    success=False,
                    error=str(e)
                ))

        return executed_calls

    def _serialize_tool_call(self, tool_call: MCPToolCall) -> Dict[str, Any]:
        """Serialize a tool call for storage in trajectory metadata"""
        return {
            "tool_name": tool_call.tool_name,
            "arguments": tool_call.arguments,
            "result": str(tool_call.result) if tool_call.result is not None else None,
            "success": tool_call.success,
            "error": tool_call.error
        }
    
    async def execute_trajectory(
        self,
        trajectory: Trajectory,
        executor: Optional[callable] = None
    ) -> Trajectory:
        """Execute the generated code and update trajectory"""
        
        if not trajectory.generated_code:
            trajectory.success = True
            trajectory.execution_result = "No code to execute"
            return trajectory
        
        try:
            if executor:
                # Use custom executor
                result = await executor(trajectory.generated_code)
                trajectory.execution_result = str(result)
                trajectory.success = True
            else:
                # Simple code execution (for demonstration)
                # In practice, you'd want a sandboxed execution environment
                exec_globals = {}
                exec_locals = {}
                
                try:
                    exec(trajectory.generated_code, exec_globals, exec_locals)
                    trajectory.execution_result = "Code executed successfully"
                    trajectory.success = True
                except Exception as e:
                    trajectory.execution_result = f"Execution error: {str(e)}"
                    trajectory.success = False
                    trajectory.error_message = str(e)
        
        except Exception as e:
            trajectory.success = False
            trajectory.error_message = str(e)
            trajectory.execution_result = f"Execution failed: {str(e)}"
        
        return trajectory
    
    async def batch_generate_trajectories(
        self,
        queries: List[str],
        playbook: Playbook,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Trajectory]:
        """Generate trajectories for multiple queries"""
        trajectories = []
        
        for query in queries:
            trajectory = await self.generate_trajectory(query, playbook, context)
            trajectory = await self.execute_trajectory(trajectory)
            trajectories.append(trajectory)
        
        return trajectories
