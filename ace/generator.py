"""
Generator Component for ACE Framework
"""
from typing import List, Dict, Any, Optional
import json
from .models import Trajectory, Playbook, Bullet, ACEConfig
from .llm_client import LLMClient


class Generator:
    """Generates reasoning trajectories using the current playbook"""
    
    def __init__(self, config: ACEConfig, llm_client: LLMClient):
        self.config = config
        self.llm_client = llm_client
    
    async def generate_trajectory(
        self,
        query: str,
        playbook: Playbook,
        context: Optional[Dict[str, Any]] = None
    ) -> Trajectory:
        """Generate a reasoning trajectory for the given query"""
        
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
        
        # Generate trajectory
        trajectory = await self._generate_trajectory_with_llm(
            query, playbook_content, context
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
        context: Optional[Dict[str, Any]]
    ) -> Trajectory:
        """Generate trajectory using LLM"""
        
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

{playbook_content}

Additional Context: {json.dumps(context, indent=2) if context else 'None'}

Please solve this problem using the playbook strategies and your reasoning."""
        
        try:
            response = await self.llm_client.generate_json_response(
                prompt,
                model=self.config.generator_model,
                temperature=0.7,
                system_prompt=system_prompt
            )
            
            trajectory = Trajectory(
                query=query,
                reasoning_steps=response.get("reasoning_steps", []),
                generated_code=response.get("generated_code"),
                metadata={
                    "confidence": response.get("confidence", 0.5),
                    "used_strategies": response.get("used_strategies", []),
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
                metadata={"error": str(e), "fallback": True}
            )
            
            return trajectory
    
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
