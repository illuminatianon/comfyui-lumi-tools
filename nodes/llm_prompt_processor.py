"""
LLM Prompt Processor node for stateless text generation.
"""

import logging
from typing import Any, Dict, Tuple

from .llm_inference import create_provider


class LumiLLMPromptProcessor:
    """Stateless LLM prompt processor that generates text using provider configuration."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "provider": (
                    "LLM_PROVIDER",
                    {"tooltip": "LLM provider configuration from a provider node"},
                ),
                "instructions": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "tooltip": "System instructions for the LLM",
                    },
                ),
                "prompt": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "tooltip": "User prompt to process",
                    },
                ),
                "seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "tooltip": "Random seed for deterministic generation (if supported by model)",
                    },
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "process_prompt"
    CATEGORY = "Lumi/LLM"

    DESCRIPTION = (
        "Processes text prompts using an LLM provider. This node is stateless and "
        "requires a provider configuration from a provider node. It combines the "
        "instructions and prompt to generate text using the configured LLM."
    )

    def process_prompt(
        self, provider: Dict[str, Any], instructions: str, prompt: str, seed: int
    ) -> Tuple[str]:
        """Process the prompt using the configured LLM provider."""

        try:
            # Validate provider configuration
            if not isinstance(provider, dict):
                raise ValueError("Invalid provider configuration: must be a dictionary")

            provider_type = provider.get("provider_type")
            if not provider_type:
                raise ValueError("Provider configuration missing 'provider_type'")

            # Extract provider parameters
            api_key = provider.get("api_key")
            model_id = provider.get("model_id")
            max_tokens = provider.get("max_tokens", 1000)
            top_p = provider.get("top_p", 1.0)

            if not api_key:
                env_key = provider.get("env_key", "OPENROUTER_API_KEY")
                raise ValueError(
                    f"API key not available. Please ensure the environment variable "
                    f"'{env_key}' is set with your API key."
                )

            if not model_id:
                raise ValueError("Model ID not specified in provider configuration")

            # Create provider instance
            llm_provider = create_provider(
                provider_type=provider_type,
                api_key=api_key,
                model_id=model_id,
                max_tokens=max_tokens,
                top_p=top_p,
            )

            # Generate text
            result = llm_provider.generate(
                instructions=instructions, prompt=prompt, seed=seed if seed > 0 else None
            )

            # Log successful generation (without sensitive data)
            model_info = provider.get("model_info", {})
            model_name = model_info.get("name", model_id)
            logging.info(f"LLM generation completed using {model_name}")

            return (result,)

        except Exception as e:
            # Log error and re-raise for ComfyUI error handling
            logging.error(f"LLM Prompt Processor error: {str(e)}")
            raise RuntimeError(f"LLM processing failed: {str(e)}") from e

    @classmethod
    def IS_CHANGED(cls, provider, instructions, prompt, seed):
        """Determine if node should be re-executed based on inputs."""
        # Always re-execute if any input changes
        return hash((str(provider), instructions, prompt, seed))
