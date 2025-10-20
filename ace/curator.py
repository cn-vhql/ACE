"""
Curator Component for ACE Framework
"""
from typing import List, Dict, Any, Optional
import json
from .models import DeltaUpdate, Reflection, Playbook, Bullet, BulletType, ACEConfig
from .llm_client import LLMClient


class Curator:
    """Curates and integrates insights into the playbook"""
    
    def __init__(self, config: ACEConfig, llm_client: LLMClient):
        self.config = config
        self.llm_client = llm_client
    
    async def create_delta_update(
        self,
        reflection: Reflection,
        playbook: Playbook,
        trajectory_context: Optional[Dict[str, Any]] = None
    ) -> DeltaUpdate:
        """Create a delta update based on a reflection"""
        
        # Analyze what new insights are missing from the current playbook
        missing_insights = await self._identify_missing_insights(reflection, playbook)
        
        if not missing_insights:
            # No new insights to add
            return DeltaUpdate(
                operations=[],
                reasoning="No new insights identified for playbook update."
            )
        
        # Generate delta update operations
        operations = await self._generate_delta_operations(missing_insights, reflection)
        
        # Update bullet counts based on reflection tags
        bullet_updates = await self._update_bullet_counts(reflection)
        operations.extend(bullet_updates)
        
        delta_update = DeltaUpdate(
            operations=operations,
            reasoning=f"Created delta update based on reflection: {reflection.key_insight or 'General improvement'}"
        )
        
        return delta_update
    
    async def _identify_missing_insights(
        self,
        reflection: Reflection,
        playbook: Playbook
    ) -> List[str]:
        """Identify insights that are missing from the current playbook"""
        
        system_prompt = """You are a master curator of knowledge. Your job is to identify what new insights should be added to an existing playbook based on a reflection.

Your task is to:
1. Review the existing playbook and the reflection
2. Identify ONLY the NEW insights, strategies, or mistakes that are MISSING from the current playbook
3. Avoid redundancy - don't suggest content that already exists
4. Focus on quality over quantity
5. Each suggestion should be actionable and specific

Always respond with a JSON object containing:
- reasoning: Your analysis process
- missing_insights: List of specific insights that should be added to the playbook
- suggested_sections: Where each insight should be placed"""
        
        # Get current playbook content
        playbook_content = self._get_playbook_summary(playbook)
        
        prompt = f"""Please analyze what insights are missing from this playbook.

CURRENT PLAYBOOK SUMMARY:
{playbook_content}

REFLECTION TO ANALYZE:
{reflection.reasoning}

KEY INSIGHT: {reflection.key_insight or 'No key insight provided'}
ERROR IDENTIFICATION: {reflection.error_identification or 'No error identified'}
ROOT CAUSE: {reflection.root_cause_analysis or 'No root cause analysis'}
CORRECT APPROACH: {reflection.correct_approach or 'No correct approach specified'}

Please identify what new insights should be added to the playbook."""
        
        try:
            response = await self.llm_client.generate_json_response(
                prompt,
                model=self.config.curator_model,
                temperature=0.3,
                system_prompt=system_prompt
            )
            
            return response.get("missing_insights", [])
            
        except Exception as e:
            # Fallback: extract key insights from reflection
            fallback_insights = []
            if reflection.key_insight:
                fallback_insights.append(reflection.key_insight)
            if reflection.correct_approach and len(reflection.correct_approach) > 20:
                fallback_insights.append(f"Strategy: {reflection.correct_approach}")
            
            return fallback_insights
    
    async def _generate_delta_operations(
        self,
        missing_insights: List[str],
        reflection: Reflection
    ) -> List[Dict[str, Any]]:
        """Generate delta operations for missing insights"""
        
        operations = []
        
        for insight in missing_insights:
            # Determine the appropriate section and bullet type
            section, bullet_type = await self._classify_insight(insight, reflection)
            
            operation = {
                "type": "ADD",
                "section": section,
                "content": insight,
                "bullet_type": bullet_type.value,
                "metadata": {
                    "source_reflection_id": reflection.id,
                    "created_from": "reflection"
                }
            }
            
            operations.append(operation)
        
        return operations
    
    async def _classify_insight(
        self,
        insight: str,
        reflection: Reflection
    ) -> tuple[str, BulletType]:
        """Classify an insight into a section and bullet type"""
        
        # Simple heuristic-based classification
        insight_lower = insight.lower()
        
        # Determine section
        if any(keyword in insight_lower for keyword in ["error", "mistake", "wrong", "incorrect"]):
            section = "error_patterns"
        elif any(keyword in insight_lower for keyword in ["strategy", "approach", "method", "technique"]):
            section = "strategies"
        elif any(keyword in insight_lower for keyword in ["api", "function", "call", "interface"]):
            section = "api_guidelines"
        elif any(keyword in insight_lower for keyword in ["verify", "check", "validate", "test"]):
            section = "verification_checklist"
        elif any(keyword in insight_lower for keyword in ["formula", "calculation", "compute", "math"]):
            section = "formulas_and_calculations"
        else:
            section = "general_insights"
        
        # Determine bullet type
        if section == "error_patterns":
            bullet_type = BulletType.ERROR_PATTERN
        elif section == "strategies":
            bullet_type = BulletType.STRATEGY
        elif section == "api_guidelines":
            bullet_type = BulletType.API_GUIDELINE
        elif section == "verification_checklist":
            bullet_type = BulletType.VERIFICATION_CHECK
        elif section == "formulas_and_calculations":
            bullet_type = BulletType.FORMULA
        else:
            bullet_type = BulletType.INSIGHT
        
        return section, bullet_type
    
    async def _update_bullet_counts(
        self,
        reflection: Reflection
    ) -> List[Dict[str, Any]]:
        """Update bullet counts based on reflection tags"""
        
        operations = []
        
        for bullet_id, tag in reflection.bullet_tags.items():
            if tag.value == "helpful":
                operations.append({
                    "type": "UPDATE_COUNT",
                    "bullet_id": bullet_id,
                    "increment_helpful": 1
                })
            elif tag.value == "harmful":
                operations.append({
                    "type": "UPDATE_COUNT",
                    "bullet_id": bullet_id,
                    "increment_harmful": 1
                })
        
        return operations
    
    def _get_playbook_summary(self, playbook: Playbook) -> str:
        """Get a summary of the current playbook content"""
        
        if not playbook.bullets:
            return "Empty playbook - no bullets exist yet."
        
        summary = f"Playbook contains {len(playbook.bullets)} bullets across {len(playbook.sections)} sections:\n\n"
        
        for section_name, bullet_ids in playbook.sections.items():
            section_bullets = [b for b in playbook.bullets if b.id in bullet_ids]
            summary += f"{section_name.upper()} ({len(section_bullets)} bullets):\n"
            
            # Show a few example bullets from each section
            for bullet in section_bullets[:3]:
                summary += f"  - [{bullet.tag().value}] {bullet.content[:100]}...\n"
            
            if len(section_bullets) > 3:
                summary += f"  ... and {len(section_bullets) - 3} more\n"
            summary += "\n"
        
        return summary
    
    async def apply_delta_update(self, playbook: Playbook, delta_update: DeltaUpdate) -> Playbook:
        """Apply a delta update to the playbook"""
        
        for operation in delta_update.operations:
            op_type = operation.get("type")
            
            if op_type == "ADD":
                await self._apply_add_operation(playbook, operation)
            elif op_type == "UPDATE_COUNT":
                await self._apply_update_count_operation(playbook, operation)
            elif op_type == "REMOVE":
                await self._apply_remove_operation(playbook, operation)
        
        # Remove duplicates and enforce size limits
        await self._deduplicate_bullets(playbook)
        await self._enforce_size_limits(playbook)
        
        return playbook
    
    async def _apply_add_operation(self, playbook: Playbook, operation: Dict[str, Any]) -> None:
        """Apply an ADD operation"""
        
        bullet = Bullet(
            content=operation["content"],
            bullet_type=BulletType(operation["bullet_type"]),
            section=operation["section"],
            metadata=operation.get("metadata", {})
        )
        
        playbook.add_bullet(bullet)
    
    async def _apply_update_count_operation(self, playbook: Playbook, operation: Dict[str, Any]) -> None:
        """Apply an UPDATE_COUNT operation"""
        
        bullet_id = operation["bullet_id"]
        
        for bullet in playbook.bullets:
            if bullet.id == bullet_id:
                if "increment_helpful" in operation:
                    bullet.helpful_count += operation["increment_helpful"]
                if "increment_harmful" in operation:
                    bullet.harmful_count += operation["increment_harmful"]
                bullet.updated_at = bullet.updated_at  # Update timestamp
                break
    
    async def _apply_remove_operation(self, playbook: Playbook, operation: Dict[str, Any]) -> None:
        """Apply a REMOVE operation"""
        
        bullet_id = operation["bullet_id"]
        
        # Remove from bullets list
        playbook.bullets = [b for b in playbook.bullets if b.id != bullet_id]
        
        # Remove from sections
        for section_bullets in playbook.sections.values():
            if bullet_id in section_bullets:
                section_bullets.remove(bullet_id)
    
    async def _deduplicate_bullets(self, playbook: Playbook) -> None:
        """Remove duplicate bullets from the playbook"""
        
        # Simple deduplication based on content similarity
        unique_bullets = []
        seen_contents = set()
        
        for bullet in playbook.bullets:
            content_key = bullet.content.lower().strip()
            
            # Check for near-duplicates
            is_duplicate = False
            for seen_content in seen_contents:
                if self._content_similarity(content_key, seen_content) > self.config.similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_bullets.append(bullet)
                seen_contents.add(content_key)
        
        playbook.bullets = unique_bullets
        
        # Rebuild sections
        new_sections = {}
        for bullet in playbook.bullets:
            if bullet.section not in new_sections:
                new_sections[bullet.section] = []
            new_sections[bullet.section].append(bullet.id)
        
        playbook.sections = new_sections
    
    def _content_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity between two content strings"""
        
        # Simple word-based similarity
        words1 = set(content1.split())
        words2 = set(content2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def _enforce_size_limits(self, playbook: Playbook) -> None:
        """Enforce size limits on the playbook"""
        
        if len(playbook.bullets) <= self.config.max_playbook_bullets:
            return
        
        # Sort bullets by a combination of helpfulness and recency
        scored_bullets = []
        for bullet in playbook.bullets:
            score = bullet.helpful_count - bullet.harmful_count
            # Add recency bonus (newer bullets get slight bonus)
            import datetime
            days_old = (datetime.datetime.now() - bullet.created_at).days
            recency_bonus = max(0, 1 - days_old / 365)  # Decay over a year
            score += recency_bonus * 0.1
            scored_bullets.append((score, bullet))
        
        # Sort by score (descending) and keep the best ones
        scored_bullets.sort(key=lambda x: x[0], reverse=True)
        
        # Keep only the top bullets
        kept_bullets = [bullet for score, bullet in scored_bullets[:self.config.max_playbook_bullets]]
        
        playbook.bullets = kept_bullets
        
        # Rebuild sections
        new_sections = {}
        for bullet in playbook.bullets:
            if bullet.section not in new_sections:
                new_sections[bullet.section] = []
            new_sections[bullet.section].append(bullet.id)
        
        playbook.sections = new_sections
    
    async def batch_create_delta_updates(
        self,
        reflections: List[Reflection],
        playbook: Playbook
    ) -> List[DeltaUpdate]:
        """Create delta updates for multiple reflections"""
        
        delta_updates = []
        
        for reflection in reflections:
            delta_update = await self.create_delta_update(reflection, playbook)
            delta_updates.append(delta_update)
        
        return delta_updates

