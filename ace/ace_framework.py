"""
Main ACE Framework Implementation
"""
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import json
from datetime import datetime
from .models import (
    ACEConfig, Playbook, Trajectory, Reflection, DeltaUpdate,
    Bullet, BulletType
)
from .llm_client import LLMClient
from .generator import Generator
from .reflector import Reflector
from .curator import Curator


class ACE:
    """
    Agentic Context Engineering Framework
    
    A framework for comprehensive context adaptation in both offline 
    and online scenarios through modular generation, reflection, 
    and curation processes.
    """
    
    def __init__(self, config: ACEConfig):
        """Initialize the ACE framework with configuration"""
        self.config = config
        self.playbook = Playbook()
        
        # Initialize components
        self.llm_client = LLMClient(config)
        self.generator = Generator(config, self.llm_client)
        self.reflector = Reflector(config, self.llm_client)
        self.curator = Curator(config, self.llm_client)
        
        # Track statistics
        self.stats = {
            "total_trajectories": 0,
            "total_reflections": 0,
            "total_delta_updates": 0,
            "successful_trajectories": 0,
            "failed_trajectories": 0
        }
    
    async def solve_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        update_playbook: bool = True
    ) -> Tuple[Trajectory, Optional[Reflection]]:
        """
        Solve a single query and optionally update the playbook
        
        Args:
            query: The problem to solve
            context: Additional context for solving the query
            update_playbook: Whether to update the playbook after solving
            
        Returns:
            Tuple of (trajectory, reflection)
        """
        
        # Generate trajectory
        trajectory = await self.generator.generate_trajectory(query, self.playbook, context)
        trajectory = await self.generator.execute_trajectory(trajectory)
        
        # Update statistics
        self.stats["total_trajectories"] += 1
        if trajectory.success:
            self.stats["successful_trajectories"] += 1
        else:
            self.stats["failed_trajectories"] += 1
        
        # Generate reflection
        reflection = await self.reflector.reflect_on_trajectory(trajectory, self.playbook)
        self.stats["total_reflections"] += 1
        
        # Update playbook if requested
        if update_playbook:
            await self.update_playbook_from_reflection(reflection)
        
        return trajectory, reflection
    
    async def solve_batch_queries(
        self,
        queries: List[str],
        contexts: Optional[List[Dict[str, Any]]] = None,
        update_playbook: bool = True
    ) -> List[Tuple[Trajectory, Reflection]]:
        """
        Solve multiple queries in batch
        
        Args:
            queries: List of problems to solve
            contexts: List of additional contexts (optional)
            update_playbook: Whether to update the playbook after solving
            
        Returns:
            List of (trajectory, reflection) tuples
        """
        
        if contexts and len(contexts) != len(queries):
            raise ValueError("Number of contexts must match number of queries")
        
        results = []
        
        for i, query in enumerate(queries):
            context = contexts[i] if contexts else None
            trajectory, reflection = await self.solve_query(query, context, update_playbook)
            results.append((trajectory, reflection))
        
        return results
    
    async def offline_adaptation(
        self,
        training_queries: List[str],
        ground_truths: Optional[List[Any]] = None,
        contexts: Optional[List[Dict[str, Any]]] = None,
        epochs: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Perform offline adaptation on training data
        
        Args:
            training_queries: List of training queries
            ground_truths: List of ground truth answers (optional)
            contexts: List of additional contexts (optional)
            epochs: Number of training epochs (defaults to config.max_epochs)
            
        Returns:
            Training statistics and results
        """
        
        epochs = epochs or self.config.max_epochs
        
        print(f"Starting offline adaptation with {len(training_queries)} queries for {epochs} epochs")
        
        training_stats = {
            "epochs_completed": 0,
            "total_queries_processed": 0,
            "initial_playbook_size": len(self.playbook.bullets),
            "final_playbook_size": 0,
            "epoch_stats": []
        }
        
        for epoch in range(epochs):
            print(f"Epoch {epoch + 1}/{epochs}")
            
            epoch_start_time = datetime.now()
            epoch_trajectories = []
            epoch_reflections = []
            
            # Process all queries in this epoch
            for i, query in enumerate(training_queries):
                context = contexts[i] if contexts else None
                ground_truth = ground_truths[i] if ground_truths and i < len(ground_truths) else None
                
                # Generate trajectory
                trajectory = await self.generator.generate_trajectory(query, self.playbook, context)
                trajectory = await self.generator.execute_trajectory(trajectory)
                epoch_trajectories.append(trajectory)
                
                # Generate reflection with ground truth if available
                reflection = await self.reflector.reflect_on_trajectory(
                    trajectory, self.playbook, ground_truth
                )
                epoch_reflections.append(reflection)
            
            # Create and apply delta updates for all reflections
            delta_updates = await self.curator.batch_create_delta_updates(
                epoch_reflections, self.playbook
            )
            
            for delta_update in delta_updates:
                await self.curator.apply_delta_update(self.playbook, delta_update)
                self.stats["total_delta_updates"] += 1
            
            # Calculate epoch statistics
            epoch_time = (datetime.now() - epoch_start_time).total_seconds()
            success_rate = sum(1 for t in epoch_trajectories if t.success) / len(epoch_trajectories)
            
            epoch_stats = {
                "epoch": epoch + 1,
                "duration_seconds": epoch_time,
                "success_rate": success_rate,
                "playbook_size": len(self.playbook.bullets),
                "delta_updates_applied": len([du for du in delta_updates if du.operations])
            }
            
            training_stats["epoch_stats"].append(epoch_stats)
            training_stats["epochs_completed"] += 1
            training_stats["total_queries_processed"] += len(training_queries)
            
            print(f"  Success rate: {success_rate:.2%}")
            print(f"  Playbook size: {len(self.playbook.bullets)} bullets")
            print(f"  Delta updates: {len([du for du in delta_updates if du.operations])}")
        
        training_stats["final_playbook_size"] = len(self.playbook.bullets)
        
        print(f"Offline adaptation completed. Playbook grew from {training_stats['initial_playbook_size']} to {training_stats['final_playbook_size']} bullets.")
        
        return training_stats
    
    async def online_adaptation(
        self,
        query: str,
        execution_feedback: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Trajectory, Reflection]:
        """
        Perform online adaptation for a single query
        
        Args:
            query: The query to solve
            execution_feedback: Feedback from execution (optional)
            context: Additional context (optional)
            
        Returns:
            Tuple of (trajectory, reflection)
        """
        
        # Solve the query
        trajectory = await self.generator.generate_trajectory(query, self.playbook, context)
        trajectory = await self.generator.execute_trajectory(trajectory)
        
        # Update statistics
        self.stats["total_trajectories"] += 1
        if trajectory.success:
            self.stats["successful_trajectories"] += 1
        else:
            self.stats["failed_trajectories"] += 1
        
        # Generate reflection with execution feedback
        reflection = await self.reflector.reflect_on_trajectory(
            trajectory, self.playbook, execution_feedback=execution_feedback
        )
        self.stats["total_reflections"] += 1
        
        # Update playbook
        await self.update_playbook_from_reflection(reflection)
        
        return trajectory, reflection
    
    async def update_playbook_from_reflection(self, reflection: Reflection) -> None:
        """Update the playbook based on a reflection"""
        
        # Create delta update
        delta_update = await self.curator.create_delta_update(reflection, self.playbook)
        
        # Apply delta update
        if delta_update.operations:
            await self.curator.apply_delta_update(self.playbook, delta_update)
            self.stats["total_delta_updates"] += 1
    
    def get_playbook_summary(self) -> Dict[str, Any]:
        """Get a summary of the current playbook"""
        
        summary = {
            "total_bullets": len(self.playbook.bullets),
            "sections": {},
            "bullet_types": {},
            "helpfulness_stats": {
                "helpful": 0,
                "harmful": 0,
                "neutral": 0
            }
        }
        
        for bullet in self.playbook.bullets:
            # Count by section
            if bullet.section not in summary["sections"]:
                summary["sections"][bullet.section] = 0
            summary["sections"][bullet.section] += 1
            
            # Count by type
            bullet_type_name = bullet.bullet_type.value
            if bullet_type_name not in summary["bullet_types"]:
                summary["bullet_types"][bullet_type_name] = 0
            summary["bullet_types"][bullet_type_name] += 1
            
            # Count by helpfulness
            tag = bullet.tag().value
            summary["helpfulness_stats"][tag] += 1
        
        return summary
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get framework statistics"""
        
        stats = self.stats.copy()
        stats.update({
            "playbook_size": len(self.playbook.bullets),
            "success_rate": (
                self.stats["successful_trajectories"] / self.stats["total_trajectories"]
                if self.stats["total_trajectories"] > 0 else 0
            ),
            "average_reflections_per_trajectory": (
                self.stats["total_reflections"] / self.stats["total_trajectories"]
                if self.stats["total_trajectories"] > 0 else 0
            )
        })
        
        return stats
    
    def save_playbook(self, filepath: str) -> None:
        """Save the playbook to a file"""
        
        playbook_dict = self.playbook.model_dump()
        
        with open(filepath, 'w') as f:
            json.dump(playbook_dict, f, indent=2, default=str)
        
        print(f"Playbook saved to {filepath}")
    
    def load_playbook(self, filepath: str) -> None:
        """Load a playbook from a file"""
        
        with open(filepath, 'r') as f:
            playbook_dict = json.load(f)
        
        self.playbook = Playbook(**playbook_dict)
        print(f"Playbook loaded from {filepath}")
    
    def reset_playbook(self) -> None:
        """Reset the playbook to empty"""
        
        self.playbook = Playbook()
        print("Playbook reset to empty")
    
    async def evaluate_performance(
        self,
        test_queries: List[str],
        ground_truths: Optional[List[Any]] = None,
        contexts: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate performance on test data (without updating playbook)
        
        Args:
            test_queries: List of test queries
            ground_truths: List of ground truth answers (optional)
            contexts: List of additional contexts (optional)
            
        Returns:
            Evaluation results
        """
        
        print(f"Evaluating performance on {len(test_queries)} test queries")
        
        results = {
            "total_queries": len(test_queries),
            "successful_queries": 0,
            "failed_queries": 0,
            "average_confidence": 0.0,
            "query_results": []
        }
        
        confidences = []
        
        for i, query in enumerate(test_queries):
            context = contexts[i] if contexts else None
            
            # Generate trajectory without updating playbook
            trajectory = await self.generator.generate_trajectory(query, self.playbook, context)
            trajectory = await self.generator.execute_trajectory(trajectory)
            
            # Extract confidence from metadata
            confidence = trajectory.metadata.get("confidence", 0.5)
            confidences.append(confidence)
            
            if trajectory.success:
                results["successful_queries"] += 1
            else:
                results["failed_queries"] += 1
            
            result_entry = {
                "query": query,
                "success": trajectory.success,
                "confidence": confidence,
                "execution_result": trajectory.execution_result,
                "error_message": trajectory.error_message
            }
            
            results["query_results"].append(result_entry)
        
        results["success_rate"] = results["successful_queries"] / results["total_queries"]
        results["average_confidence"] = sum(confidences) / len(confidences) if confidences else 0
        
        print(f"Evaluation completed. Success rate: {results['success_rate']:.2%}")
        
        return results
