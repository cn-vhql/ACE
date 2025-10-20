"""
Tests for ACE Framework
"""
import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, patch
from ace import ACE, ACEConfig, Playbook, Bullet, BulletType, BulletTag


class TestACEConfig:
    """Test ACE configuration"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = ACEConfig()
        
        assert config.generator_model == "gpt-4"
        assert config.reflector_model == "gpt-4"
        assert config.curator_model == "gpt-4"
        assert config.max_reflector_rounds == 3
        assert config.max_epochs == 5
        assert config.max_playbook_bullets == 1000
        assert config.similarity_threshold == 0.8
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = ACEConfig(
            generator_model="gpt-3.5-turbo",
            max_reflector_rounds=2,
            max_epochs=3
        )
        
        assert config.generator_model == "gpt-3.5-turbo"
        assert config.max_reflector_rounds == 2
        assert config.max_epochs == 3


class TestBullet:
    """Test Bullet functionality"""
    
    def test_bullet_creation(self):
        """Test creating a bullet"""
        bullet = Bullet(
            content="Test strategy",
            bullet_type=BulletType.STRATEGY,
            section="strategies"
        )
        
        assert bullet.content == "Test strategy"
        assert bullet.bullet_type == BulletType.STRATEGY
        assert bullet.section == "strategies"
        assert bullet.helpful_count == 0
        assert bullet.harmful_count == 0
        assert bullet.tag() == BulletTag.NEUTRAL
    
    def test_bullet_tagging(self):
        """Test bullet tagging based on counts"""
        # Helpful bullet
        helpful_bullet = Bullet(
            content="Helpful strategy",
            bullet_type=BulletType.STRATEGY,
            section="strategies",
            helpful_count=5,
            harmful_count=1
        )
        assert helpful_bullet.tag() == BulletTag.HELPFUL
        
        # Harmful bullet
        harmful_bullet = Bullet(
            content="Harmful strategy",
            bullet_type=BulletType.STRATEGY,
            section="strategies",
            helpful_count=1,
            harmful_count=5
        )
        assert harmful_bullet.tag() == BulletTag.HARMFUL
        
        # Neutral bullet
        neutral_bullet = Bullet(
            content="Neutral strategy",
            bullet_type=BulletType.STRATEGY,
            section="strategies",
            helpful_count=2,
            harmful_count=2
        )
        assert neutral_bullet.tag() == BulletTag.NEUTRAL


class TestPlaybook:
    """Test Playbook functionality"""
    
    def test_empty_playbook(self):
        """Test empty playbook"""
        playbook = Playbook()
        
        assert len(playbook.bullets) == 0
        assert len(playbook.sections) == 0
    
    def test_add_bullet(self):
        """Test adding bullets to playbook"""
        playbook = Playbook()
        bullet = Bullet(
            content="Test strategy",
            bullet_type=BulletType.STRATEGY,
            section="strategies"
        )
        
        playbook.add_bullet(bullet)
        
        assert len(playbook.bullets) == 1
        assert len(playbook.sections) == 1
        assert "strategies" in playbook.sections
        assert bullet.id in playbook.sections["strategies"]
    
    def test_get_bullets_by_section(self):
        """Test retrieving bullets by section"""
        playbook = Playbook()
        
        strategy_bullet = Bullet(
            content="Strategy 1",
            bullet_type=BulletType.STRATEGY,
            section="strategies"
        )
        error_bullet = Bullet(
            content="Error pattern",
            bullet_type=BulletType.ERROR_PATTERN,
            section="errors"
        )
        
        playbook.add_bullet(strategy_bullet)
        playbook.add_bullet(error_bullet)
        
        strategies = playbook.get_bullets_by_section("strategies")
        errors = playbook.get_bullets_by_section("errors")
        
        assert len(strategies) == 1
        assert len(errors) == 1
        assert strategies[0].content == "Strategy 1"
        assert errors[0].content == "Error pattern"
    
    def test_get_relevant_bullets(self):
        """Test retrieving relevant bullets based on query"""
        playbook = Playbook()
        
        python_bullet = Bullet(
            content="Python function for factorial",
            bullet_type=BulletType.STRATEGY,
            section="strategies"
        )
        math_bullet = Bullet(
            content="Mathematical formula for area",
            bullet_type=BulletType.FORMULA,
            section="formulas"
        )
        
        playbook.add_bullet(python_bullet)
        playbook.add_bullet(math_bullet)
        
        # Query about Python should return the Python bullet
        relevant = playbook.get_relevant_bullets("python factorial")
        assert len(relevant) == 1
        assert "python" in relevant[0].content.lower()


class TestACEFramework:
    """Test ACE Framework integration"""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration"""
        return ACEConfig(
            generator_model="gpt-3.5-turbo",
            reflector_model="gpt-3.5-turbo",
            curator_model="gpt-3.5-turbo",
            openai_api_key="test-key"
        )
    
    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client"""
        mock_client = Mock()
        mock_client.generate_response = AsyncMock(return_value="Test response")
        mock_client.generate_json_response = AsyncMock(return_value={
            "reasoning_steps": ["Step 1", "Step 2"],
            "generated_code": "def test(): pass",
            "confidence": 0.8,
            "used_strategies": []
        })
        return mock_client
    
    @patch('ace.llm_client.OpenAI')
    @patch('ace.llm_client.Anthropic')
    def test_ace_initialization(self, mock_anthropic, mock_openai, mock_config):
        """Test ACE initialization"""
        # Mock the API clients
        mock_openai.return_value = Mock()
        mock_anthropic.return_value = Mock()
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            ace = ACE(mock_config)
            
            assert ace.config == mock_config
            assert isinstance(ace.playbook, Playbook)
            assert ace.llm_client is not None
            assert ace.generator is not None
            assert ace.reflector is not None
            assert ace.curator is not None
    
    def test_get_playbook_summary(self, mock_config):
        """Test getting playbook summary"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            ace = ACE(mock_config)
            
            # Add some bullets
            bullet1 = Bullet(
                content="Strategy 1",
                bullet_type=BulletType.STRATEGY,
                section="strategies",
                helpful_count=5
            )
            bullet2 = Bullet(
                content="Error pattern",
                bullet_type=BulletType.ERROR_PATTERN,
                section="errors",
                harmful_count=2
            )
            
            ace.playbook.add_bullet(bullet1)
            ace.playbook.add_bullet(bullet2)
            
            summary = ace.get_playbook_summary()
            
            assert summary["total_bullets"] == 2
            assert "strategies" in summary["sections"]
            assert "errors" in summary["sections"]
            assert summary["sections"]["strategies"] == 1
            assert summary["sections"]["errors"] == 1
            assert summary["helpfulness_stats"]["helpful"] == 1
            assert summary["helpfulness_stats"]["harmful"] == 1
    
    def test_get_statistics(self, mock_config):
        """Test getting framework statistics"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            ace = ACE(mock_config)
            
            # Update some stats
            ace.stats["total_trajectories"] = 10
            ace.stats["successful_trajectories"] = 7
            ace.stats["total_reflections"] = 10
            
            stats = ace.get_statistics()
            
            assert stats["total_trajectories"] == 10
            assert stats["successful_trajectories"] == 7
            assert stats["success_rate"] == 0.7
            assert stats["playbook_size"] == 0  # Empty playbook
    
    def test_save_and_load_playbook(self, mock_config, tmp_path):
        """Test saving and loading playbook"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            ace = ACE(mock_config)
            
            # Add a bullet
            bullet = Bullet(
                content="Test strategy",
                bullet_type=BulletType.STRATEGY,
                section="strategies"
            )
            ace.playbook.add_bullet(bullet)
            
            # Save playbook
            playbook_path = tmp_path / "test_playbook.json"
            ace.save_playbook(str(playbook_path))
            
            # Create new ACE instance and load playbook
            ace2 = ACE(mock_config)
            ace2.load_playbook(str(playbook_path))
            
            assert len(ace2.playbook.bullets) == 1
            assert ace2.playbook.bullets[0].content == "Test strategy"
    
    def test_reset_playbook(self, mock_config):
        """Test resetting playbook"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            ace = ACE(mock_config)
            
            # Add a bullet
            bullet = Bullet(
                content="Test strategy",
                bullet_type=BulletType.STRATEGY,
                section="strategies"
            )
            ace.playbook.add_bullet(bullet)
            
            assert len(ace.playbook.bullets) == 1
            
            # Reset playbook
            ace.reset_playbook()
            
            assert len(ace.playbook.bullets) == 0


class TestIntegration:
    """Integration tests for ACE Framework"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test end-to-end workflow with mocked LLM responses"""
        
        # Mock configuration
        config = ACEConfig(
            generator_model="gpt-3.5-turbo",
            reflector_model="gpt-3.5-turbo",
            curator_model="gpt-3.5-turbo",
            openai_api_key="test-key",
            max_reflector_rounds=1,
            max_epochs=1
        )
        
        # Mock LLM responses
        with patch('ace.llm_client.OpenAI'), \
             patch('ace.llm_client.Anthropic'), \
             patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            
            ace = ACE(config)
            
            # Mock the LLM client methods
            ace.llm_client.generate_json_response = AsyncMock(side_effect=[
                # Generator response
                {
                    "reasoning_steps": ["Define factorial function", "Implement recursive solution"],
                    "generated_code": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n-1)",
                    "confidence": 0.9,
                    "used_strategies": ["recursive_approach"]
                },
                # Reflector response
                {
                    "reasoning": "The function was implemented correctly",
                    "error_identification": None,
                    "root_cause_analysis": None,
                    "correct_approach": None,
                    "key_insight": "Recursive solutions work well for factorial",
                    "bullet_tags": {}
                },
                # Curator response
                {
                    "reasoning": "Adding new insight about recursive factorial",
                    "missing_insights": ["Use recursive approach for factorial problems"],
                    "suggested_sections": {"strategies": ["strategies"]}
                }
            ])
            
            # Test solving a query
            query = "Write a factorial function"
            trajectory, reflection = await ace.solve_query(query)
            
            assert trajectory.query == query
            assert len(trajectory.reasoning_steps) > 0
            assert trajectory.generated_code is not None
            assert reflection.trajectory_id == trajectory.id
            
            # Check that playbook was updated
            assert len(ace.playbook.bullets) > 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

