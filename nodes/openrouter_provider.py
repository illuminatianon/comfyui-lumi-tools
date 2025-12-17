"""
OpenRouter Provider node for LLM configuration.
"""

import os
from typing import Any, Dict, Tuple

from .llm_models import model_cache


class LumiOpenRouterProvider:
    """OpenRouter provider node that manages API configuration and model selection."""

    @classmethod
    def INPUT_TYPES(cls):
        # Initialize model cache to get available models
        model_cache.initialize()
        model_choices = model_cache.get_model_choices("openrouter")

        # Ensure we have at least one model choice
        if not model_choices:
            model_choices = ["openai/gpt-4o"]

        return {
            "required": {
                "env_key": (
                    "STRING",
                    {
                        "default": "OPENROUTER_API_KEY",
                        "tooltip": "Environment variable name containing the OpenRouter API key",
                    },
                ),
                "model": (
                    model_choices,
                    {
                        "default": model_choices[0] if model_choices else "openai/gpt-4o",
                        "tooltip": "Select the OpenRouter model to use",
                    },
                ),
                "max_tokens": (
                    "INT",
                    {
                        "default": 1000,
                        "min": 1,
                        "max": 32000,
                        "step": 1,
                        "tooltip": "Maximum number of tokens to generate",
                    },
                ),
                "top_p": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.01,
                        "tooltip": "Top-p sampling parameter for response diversity",
                    },
                ),
            }
        }

    RETURN_TYPES = ("LLM_PROVIDER",)
    RETURN_NAMES = ("provider",)
    FUNCTION = "create_provider"
    CATEGORY = "Lumi/LLM"

    DESCRIPTION = (
        "Creates an OpenRouter provider configuration for LLM processing. "
        "The API key must be set as an environment variable for security. "
        "This provider configuration is passed to the LLM Prompt Processor node."
    )

    def create_provider(
        self, env_key: str, model: str, max_tokens: int, top_p: float
    ) -> Tuple[Dict[str, Any]]:
        """Create OpenRouter provider configuration."""

        # Get API key from environment
        api_key = os.getenv(env_key.strip())
        if not api_key:
            raise ValueError(
                f"API key not found in environment variable '{env_key}'. "
                f"Please set the environment variable with your OpenRouter API key."
            )

        # Validate model exists in cache
        model_info = model_cache.get_model_by_id(model, "openrouter")
        if not model_info:
            # If model not found in cache, still allow it (might be a new model)
            model_info = {"id": model, "name": f"Model: {model}"}

        # Create provider configuration
        provider_config = {
            "provider_type": "openrouter",
            "api_key": api_key,  # This will not be serialized in workflow
            "model_id": model,
            "model_info": model_info,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "env_key": env_key,  # Store for reference but don't expose the actual key
        }

        return (provider_config,)

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Always consider this node changed to prevent caching of API keys."""
        return float("nan")  # Always execute, never cache

    def __getstate__(self):
        """Custom serialization to exclude sensitive data from workflow files."""
        # Return minimal state that doesn't include API keys
        return {"class_type": self.__class__.__name__, "version": "1.0"}

    def __setstate__(self, state):
        """Custom deserialization."""
        # Nothing to restore since we don't store sensitive data
        pass
