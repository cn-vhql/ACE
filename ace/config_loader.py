"""
Configuration Loader for ACE Framework
"""
import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
import re
from .models import ACEConfig


class ConfigLoader:
    """Loads and manages configuration from YAML files"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config loader
        
        Args:
            config_path: Path to config file. If None, looks for config.yaml in current directory
        """
        if config_path is None:
            # Look for config.yaml in current directory and parent directories
            current_dir = Path.cwd()
            while current_dir != current_dir.parent:
                potential_config = current_dir / "config.yaml"
                if potential_config.exists():
                    config_path = str(potential_config)
                    break
                current_dir = current_dir.parent
            
            # If still not found, try default location
            if config_path is None:
                default_config = Path("config.yaml")
                if default_config.exists():
                    config_path = str(default_config)
        
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_path or not os.path.exists(self.config_path):
            print(f"⚠️  Config file not found at {self.config_path}, using defaults")
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Substitute environment variables
            config = self._substitute_env_vars(config)
            
            print(f"✅ Loaded configuration from {self.config_path}")
            return config
            
        except Exception as e:
            print(f"❌ Error loading config from {self.config_path}: {e}")
            print("⚠️  Using default configuration")
            return self._get_default_config()
    
    def _substitute_env_vars(self, obj: Any) -> Any:
        """Recursively substitute environment variables in configuration"""
        if isinstance(obj, dict):
            return {k: self._substitute_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            # Replace ${VAR_NAME} with environment variable
            pattern = r'\$\{([^}]+)\}'
            def replace_var(match):
                var_name = match.group(1)
                return os.getenv(var_name, match.group(0))  # Return original if not found
            return re.sub(pattern, replace_var, obj)
        else:
            return obj
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "llm_provider": {
                "type": "openai",
                "openai": {
                    "base_url": "https://api.openai.com/v1",
                    "api_key": "${OPENAI_API_KEY}",
                    "default_model": "gpt-4"
                }
            },
            "models": {
                "generator": {
                    "model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 4096
                },
                "reflector": {
                    "model": "gpt-4",
                    "temperature": 0.3,
                    "max_tokens": 4096
                },
                "curator": {
                    "model": "gpt-4",
                    "temperature": 0.2,
                    "max_tokens": 4096
                }
            },
            "ace": {
                "max_reflector_rounds": 3,
                "max_epochs": 5,
                "max_playbook_bullets": 1000,
                "similarity_threshold": 0.8,
                "max_retrieved_bullets": 10,
                "min_bullet_helpfulness": 0
            },
            "execution": {
                "timeout": 30,
                "enable_execution": True,
                "sandbox": {"enabled": False}
            },
            "logging": {
                "level": "INFO",
                "file": "ace.log",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }
    
    def get_ace_config(self) -> ACEConfig:
        """Convert YAML config to ACEConfig object"""
        ace_config = self.config.get("ace", {})
        
        # Get provider configuration
        provider_config = self.config.get("llm_provider", {})
        provider_type = provider_config.get("type", "openai")
        
        # Get model configurations
        models_config = self.config.get("models", {})
        
        # Extract model names and settings
        generator_config = models_config.get("generator", {})
        reflector_config = models_config.get("reflector", {})
        curator_config = models_config.get("curator", {})
        
        # Create ACEConfig
        config = ACEConfig(
            # Model settings
            generator_model=generator_config.get("model", "gpt-4"),
            reflector_model=reflector_config.get("model", "gpt-4"),
            curator_model=curator_config.get("model", "gpt-4"),
            
            # API settings based on provider type
            **self._get_provider_api_config(provider_type, provider_config),
            
            # ACE parameters
            max_reflector_rounds=ace_config.get("max_reflector_rounds", 3),
            max_epochs=ace_config.get("max_epochs", 5),
            max_playbook_bullets=ace_config.get("max_playbook_bullets", 1000),
            similarity_threshold=ace_config.get("similarity_threshold", 0.8),
            
            # Retrieval parameters
            max_retrieved_bullets=ace_config.get("max_retrieved_bullets", 10),
            min_bullet_helpfulness=ace_config.get("min_bullet_helpfulness", 0),
            
            # Store full config for reference
            **{
                "provider_type": provider_type,
                "provider_config": provider_config,
                "models_config": models_config,
                "execution_config": self.config.get("execution", {}),
                "logging_config": self.config.get("logging", {}),
                "mcp_config": self.config.get("mcp", {"enabled": False, "servers": {}})
            }
        )
        
        return config
    
    def _get_provider_api_config(self, provider_type: str, provider_config: Dict[str, Any]) -> Dict[str, str]:
        """Get API configuration based on provider type"""
        if provider_type == "openai":
            openai_config = provider_config.get("openai", {})
            return {
                "openai_api_key": openai_config.get("api_key"),
                "openai_base_url": openai_config.get("base_url")
            }
        elif provider_type == "anthropic":
            anthropic_config = provider_config.get("anthropic", {})
            return {
                "anthropic_api_key": anthropic_config.get("api_key"),
                "anthropic_base_url": anthropic_config.get("base_url")
            }
        elif provider_type == "custom":
            custom_config = provider_config.get("custom", {})
            # For custom providers, use OpenAI-compatible interface
            return {
                "openai_api_key": custom_config.get("api_key"),
                "openai_base_url": custom_config.get("base_url")
            }
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")
    
    def get_model_config(self, model_type: str) -> Dict[str, Any]:
        """Get configuration for a specific model type"""
        models_config = self.config.get("models", {})
        return models_config.get(model_type, {})
    
    def get_execution_config(self) -> Dict[str, Any]:
        """Get execution configuration"""
        return self.config.get("execution", {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.config.get("logging", {})
    
    def save_config(self, path: str) -> None:
        """Save current configuration to file"""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            print(f"✅ Configuration saved to {path}")
        except Exception as e:
            print(f"❌ Error saving configuration: {e}")
    
    def reload_config(self) -> None:
        """Reload configuration from file"""
        self.config = self._load_config()
        print(f"✅ Configuration reloaded from {self.config_path}")


def load_config(config_path: Optional[str] = None) -> ConfigLoader:
    """Load configuration from file"""
    return ConfigLoader(config_path)


def get_ace_config(config_path: Optional[str] = None) -> ACEConfig:
    """Get ACE configuration from file"""
    loader = ConfigLoader(config_path)
    return loader.get_ace_config()

