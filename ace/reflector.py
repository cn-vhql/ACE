"""
Reflector Component for ACE Framework
"""
from typing import List, Dict, Any, Optional
import json
from .models import Reflection, Trajectory, Playbook, Bullet, BulletTag, ACEConfig
from .llm_client import LLMClient


class Reflector:
    """Reflects on trajectories to extract insights and lessons"""
    
    def __init__(self, config: ACEConfig, llm_client: LLMClient):
        self.config = config
        self.llm_client = llm_client
    
    async def reflect_on_trajectory(
        self,
        trajectory: Trajectory,
        playbook: Playbook,
        ground_truth: Optional[Any] = None,
        execution_feedback: Optional[str] = None
    ) -> Reflection:
        """Generate a reflection on the given trajectory"""
        
        # Get the bullets that were used in this trajectory
        used_bullets = [
            bullet for bullet in playbook.bullets
            if bullet.id in trajectory.used_bullet_ids
        ]
        
        # Generate initial reflection
        reflection = await self._generate_reflection_with_llm(
            trajectory, used_bullets, ground_truth, execution_feedback
        )
        
        # Iterative refinement
        for round_num in range(self.config.max_reflector_rounds - 1):
            refined_reflection = await self._refine_reflection(
                reflection, trajectory, used_bullets, round_num + 1
            )
            
            # Check if refinement improved the reflection
            if await self._is_reflection_improved(reflection, refined_reflection):
                reflection = refined_reflection
            else:
                break
        
        return reflection
    
    async def _generate_reflection_with_llm(
        self,
        trajectory: Trajectory,
        used_bullets: List[Bullet],
        ground_truth: Optional[Any],
        execution_feedback: Optional[str]
    ) -> Reflection:
        """Generate initial reflection using LLM"""
        
        system_prompt = """You are an expert analyst and educator. Your job is to diagnose why a model's reasoning went wrong by analyzing the gap between predicted results and expected outcomes.

Your task is to:
1. Carefully analyze the model's reasoning trajectory
2. Identify what went wrong (or could be better)
3. Determine the root cause of any errors
4. Provide actionable insights for improvement
5. Tag the playbook bullets that were used as helpful, harmful, or neutral

Always respond with a valid JSON object containing:
- reasoning: Your detailed analysis and thinking process
- error_identification: What specifically went wrong
- root_cause_analysis: Why the error occurred and what concept was misunderstood
- correct_approach: What should have been done instead
- key_insight: What strategy, formula, or principle should be remembered
- bullet_tags: Dictionary mapping bullet IDs to tags ("helpful", "harmful", "neutral")"""
        
        # Format trajectory information
        trajectory_info = self._format_trajectory_for_reflection(trajectory)
        bullets_info = self._format_bullets_for_reflection(used_bullets)
        
        prompt = f"""Please analyze this reasoning trajectory and provide a detailed reflection.

TRAJECTORY INFORMATION:
{trajectory_info}

USED PLAYBOOK BULLETS:
{bullets_info}

GROUND TRUTH: {json.dumps(ground_truth, indent=2) if ground_truth is not None else 'Not provided'}

EXECUTION FEEDBACK: {execution_feedback or 'No execution feedback available'}

Please provide your analysis as a JSON object."""
        
        try:
            response = await self.llm_client.generate_json_response(
                prompt,
                model=self.config.reflector_model,
                temperature=0.3,
                system_prompt=system_prompt
            )
            
            # Parse bullet tags
            bullet_tags = {}
            for bullet_id, tag_str in response.get("bullet_tags", {}).items():
                try:
                    bullet_tags[bullet_id] = BulletTag(tag_str.lower())
                except ValueError:
                    bullet_tags[bullet_id] = BulletTag.NEUTRAL
            
            reflection = Reflection(
                trajectory_id=trajectory.id,
                reasoning=response.get("reasoning", ""),
                error_identification=response.get("error_identification"),
                root_cause_analysis=response.get("root_cause_analysis"),
                correct_approach=response.get("correct_approach"),
                key_insight=response.get("key_insight"),
                bullet_tags=bullet_tags,
                metadata={"raw_response": response}
            )
            
            return reflection
            
        except Exception as e:
            # Fallback reflection
            reflection = Reflection(
                trajectory_id=trajectory.id,
                reasoning=f"Failed to generate detailed reflection: {str(e)}",
                metadata={"error": str(e), "fallback": True}
            )
            return reflection
    
    async def _refine_reflection(
        self,
        reflection: Reflection,
        trajectory: Trajectory,
        used_bullets: List[Bullet],
        round_num: int
    ) -> Reflection:
        """Refine an existing reflection"""
        
        system_prompt = """You are refining a previous reflection to make it more insightful and actionable.
Focus on making the analysis more precise, the root causes clearer, and the insights more actionable."""
        
        prompt = f"""Please refine this reflection to make it more insightful and actionable.

ORIGINAL REFLECTION (Round {round_num - 1}):
{reflection.reasoning}

ERROR IDENTIFICATION: {reflection.error_identification or 'Not specified'}
ROOT CAUSE: {reflection.root_cause_analysis or 'Not specified'}
CORRECT APPROACH: {reflection.correct_approach or 'Not specified'}
KEY INSIGHT: {reflection.key_insight or 'Not specified'}

TRAJECTORY:
{self._format_trajectory_for_reflection(trajectory)}

Please provide an improved reflection as a JSON object with the same structure."""
        
        try:
            response = await self.llm_client.generate_json_response(
                prompt,
                model=self.config.reflector_model,
                temperature=0.2,
                system_prompt=system_prompt
            )
            
            # Update bullet tags if provided
            bullet_tags = reflection.bullet_tags.copy()
            new_bullet_tags = response.get("bullet_tags", {})
            for bullet_id, tag_str in new_bullet_tags.items():
                try:
                    bullet_tags[bullet_id] = BulletTag(tag_str.lower())
                except ValueError:
                    pass
            
            refined_reflection = Reflection(
                trajectory_id=trajectory.id,
                reasoning=response.get("reasoning", reflection.reasoning),
                error_identification=response.get("error_identification", reflection.error_identification),
                root_cause_analysis=response.get("root_cause_analysis", reflection.root_cause_analysis),
                correct_approach=response.get("correct_approach", reflection.correct_approach),
                key_insight=response.get("key_insight", reflection.key_insight),
                bullet_tags=bullet_tags,
                metadata={
                    "round": round_num,
                    "raw_response": response,
                    "previous_reflection": reflection.metadata
                }
            )
            
            return refined_reflection
            
        except Exception as e:
            # Return original reflection if refinement fails
            return reflection
    
    async def _is_reflection_improved(
        self,
        original: Reflection,
        refined: Reflection
    ) -> bool:
        """Check if the refined reflection is better than the original"""
        
        # Simple heuristic: longer reasoning and more specific analysis
        if len(refined.reasoning) <= len(original.reasoning):
            return False
        
        # Check if refined reflection has more complete fields
        original_completeness = sum([
            1 for field in [original.error_identification, original.root_cause_analysis, 
                          original.correct_approach, original.key_insight]
            if field and len(field.strip()) > 10
        ])
        
        refined_completeness = sum([
            1 for field in [refined.error_identification, refined.root_cause_analysis,
                          refined.correct_approach, refined.key_insight]
            if field and len(field.strip()) > 10
        ])
        
        return refined_completeness >= original_completeness
    
    def _format_trajectory_for_reflection(self, trajectory: Trajectory) -> str:
        """Format trajectory information for reflection"""
        
        info = f"Query: {trajectory.query}\n\n"
        info += "Reasoning Steps:\n"
        for i, step in enumerate(trajectory.reasoning_steps, 1):
            info += f"{i}. {step}\n"
        
        if trajectory.generated_code:
            info += f"\nGenerated Code:\n```\n{trajectory.generated_code}\n```\n"
        
        info += f"\nSuccess: {trajectory.success}\n"
        
        if trajectory.execution_result:
            info += f"Execution Result: {trajectory.execution_result}\n"
        
        if trajectory.error_message:
            info += f"Error Message: {trajectory.error_message}\n"
        
        return info
    
    def _format_bullets_for_reflection(self, bullets: List[Bullet]) -> str:
        """Format bullets for reflection"""
        
        if not bullets:
            return "No bullets were used in this trajectory."
        
        info = "Used Playbook Bullets:\n"
        for bullet in bullets:
            tag = bullet.tag().value.upper()
            info += f"[{bullet.id}] [{tag}] {bullet.content}\n"
        
        return info
    
    async def batch_reflect_on_trajectories(
        self,
        trajectories: List[Trajectory],
        playbook: Playbook,
        ground_truths: Optional[List[Any]] = None,
        execution_feedbacks: Optional[List[str]] = None
    ) -> List[Reflection]:
        """Generate reflections for multiple trajectories"""
        
        reflections = []
        
        for i, trajectory in enumerate(trajectories):
            ground_truth = ground_truths[i] if ground_truths and i < len(ground_truths) else None
            feedback = execution_feedbacks[i] if execution_feedbacks and i < len(execution_feedbacks) else None
            
            reflection = await self.reflect_on_trajectory(trajectory, playbook, ground_truth, feedback)
            reflections.append(reflection)
        
        return reflections

