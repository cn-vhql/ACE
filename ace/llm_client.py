"""
LLM Client for ACE Framework
"""
import os
from typing import Dict, Any, Optional, List
import openai
from openai import OpenAI
import anthropic
from anthropic import Anthropic
from .models import ACEConfig


class LLMClient:
    """Unified LLM client supporting multiple providers"""
    
    def __init__(self, config: ACEConfig):
        self.config = config
        self.openai_client = None
        self.anthropic_client = None
        self.provider_type = getattr(config, 'provider_type', 'openai')
        
        # Initialize clients based on provider type
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize LLM clients based on configuration"""
        
        if self.provider_type in ["openai", "custom"]:
            # For custom providers like ModelScope, use OpenAI-compatible interface
            api_key = getattr(self.config, 'openai_api_key', None) or os.getenv("OPENAI_API_KEY")
            base_url = getattr(self.config, 'openai_base_url', None) or "https://api.openai.com/v1"
            
            if api_key:
                self.openai_client = OpenAI(
                    api_key=api_key,
                    base_url=base_url
                )
                print(f"✅ Initialized {self.provider_type} client with base_url: {base_url}")
            else:
                print(f"⚠️  No API key found for {self.provider_type} provider")
        
        elif self.provider_type == "anthropic":
            api_key = getattr(self.config, 'anthropic_api_key', None) or os.getenv("ANTHROPIC_API_KEY")
            base_url = getattr(self.config, 'anthropic_base_url', None)
            
            if api_key:
                client_kwargs = {"api_key": api_key}
                if base_url:
                    client_kwargs["base_url"] = base_url
                
                self.anthropic_client = Anthropic(**client_kwargs)
                print(f"✅ Initialized Anthropic client")
            else:
                print("⚠️  No API key found for Anthropic provider")
    
    def _is_openai_model(self, model: str) -> bool:
        """Check if model is from OpenAI"""
        return model.startswith(("gpt-", "text-", "davinci-", "curie-", "babbage-", "ada-"))
    
    def _is_anthropic_model(self, model: str) -> bool:
        """Check if model is from Anthropic"""
        return model.startswith(("claude-",))
    
    def _should_use_openai_interface(self, model: str) -> bool:
        """Check if model should use OpenAI-compatible interface"""
        # Use OpenAI interface for OpenAI models and custom providers
        return (self._is_openai_model(model) or 
                self.provider_type in ["custom"])
    
    async def generate_response(
        self, 
        prompt: str, 
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate response from the specified model"""
        model = model or self.config.generator_model
        
        if self._should_use_openai_interface(model):
            return await self._generate_openai_response(
                prompt, model, temperature, max_tokens, system_prompt
            )
        elif self._is_anthropic_model(model):
            return await self._generate_anthropic_response(
                prompt, model, temperature, max_tokens, system_prompt
            )
        else:
            raise ValueError(f"Unsupported model: {model}")
    
    async def _generate_openai_response(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        system_prompt: Optional[str]
    ) -> str:
        """Generate response using OpenAI"""
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Get model configuration for extra parameters
        model_config = self._get_model_config_for_model(model)
        
        # Prepare create parameters
        create_params = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False  # We'll handle streaming separately if needed
        }
        
        # Add extra_body for thinking control (ModelScope specific)
        # Note: enable_thinking only works with stream=True for ModelScope
        if "extra_body" in model_config:
            extra_body = model_config["extra_body"].copy()
            # Ensure enable_thinking is explicitly set to false for non-stream calls
            extra_body["enable_thinking"] = False
            # Remove thinking_budget as it's not needed when thinking is disabled
            if "thinking_budget" in extra_body:
                extra_body.pop("thinking_budget", None)
            if extra_body:  # Only add if there are remaining parameters
                create_params["extra_body"] = extra_body
        
        try:
            response = self.openai_client.chat.completions.create(**create_params)
            content = response.choices[0].message.content
            
            # Handle thinking content if present (ModelScope specific)
            if hasattr(response.choices[0].message, 'reasoning_content'):
                thinking_content = response.choices[0].message.reasoning_content
                if thinking_content:
                    # For now, we'll append thinking to the response
                    # In a more sophisticated implementation, you might want to handle this differently
                    content = f"Thinking: {thinking_content}\n\nAnswer: {content}"
            
            return content or ""
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")
    
    def _get_model_config_for_model(self, model: str) -> Dict[str, Any]:
        """Get model configuration for a specific model"""
        models_config = getattr(self.config, 'models_config', {})
        
        # Find which model type this belongs to
        for model_type, config in models_config.items():
            if config.get("model") == model:
                return config
        
        # Return empty config if not found
        return {}
    
    async def _generate_anthropic_response(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: Optional[int],
        system_prompt: Optional[str]
    ) -> str:
        """Generate response using Anthropic"""
        if not self.anthropic_client:
            raise ValueError("Anthropic client not initialized")
        
        try:
            if system_prompt:
                message = self.anthropic_client.messages.create(
                    model=model,
                    max_tokens=max_tokens or 4096,
                    temperature=temperature,
                    system=system_prompt,
                    messages=[{"role": "user", "content": prompt}]
                )
            else:
                message = self.anthropic_client.messages.create(
                    model=model,
                    max_tokens=max_tokens or 4096,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
            return message.content[0].text
        except Exception as e:
            raise RuntimeError(f"Anthropic API error: {e}")
    
    async def generate_json_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.3,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate JSON response from the specified model"""
        model = model or self.config.generator_model
        
        # Add JSON formatting instruction to prompt
        json_prompt = f"""{prompt}

Please respond with a valid JSON object only. Do not include any markdown formatting or explanations."""
        
        response = await self.generate_response(
            json_prompt, model, temperature, system_prompt=system_prompt
        )
        
        try:
            import json
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError(f"Failed to parse JSON response: {response}")
