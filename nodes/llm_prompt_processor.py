"""
LLM Prompt Processor node for stateless text generation.
"""

import logging
from typing import Any, Dict, Tuple

from .llm_inference import create_provider
from .v3_types import LLM_PROVIDER_TYPE

try:
    from comfy_api.latest import io
except ImportError:
    io = None


_ComfyNodeBase = io.ComfyNode if io is not None else object

try:
    import comfy.model_management as model_management  # type: ignore[import-not-found]

    HAS_MODEL_MANAGEMENT = True
except ImportError:
    model_management = None
    HAS_MODEL_MANAGEMENT = False


def _is_processing_interrupt_exception(error: Exception) -> bool:
    """Return True when the error is ComfyUI's interrupt exception."""
    if error.__class__.__name__ == "InterruptProcessingException":
        return True

    if HAS_MODEL_MANAGEMENT and model_management is not None:
        interrupt_error = getattr(model_management, "InterruptProcessingException", None)
        if interrupt_error is not None and isinstance(error, interrupt_error):
            return True

    return False


class LumiLLMPromptProcessor(_ComfyNodeBase):
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
    FUNCTION = "execute"
    CATEGORY = "Lumi/LLM"

    DESCRIPTION = (
        "Processes text prompts using an LLM provider. This node is stateless and "
        "requires a provider configuration from a provider node. It combines the "
        "instructions and prompt to generate text using the configured LLM."
    )

    @classmethod
    def define_schema(cls):
        if io is None or LLM_PROVIDER_TYPE is None:
            raise RuntimeError("ComfyUI V3 API is not available")

        return io.Schema(
            node_id="LumiLLMPromptProcessor",
            display_name="Lumi LLM Prompt Processor",
            category="Lumi/LLM",
            description=cls.DESCRIPTION,
            inputs=[
                LLM_PROVIDER_TYPE.Input(
                    "provider",
                    tooltip="LLM provider configuration from a provider node",
                ),
                io.String.Input(
                    "instructions",
                    default="",
                    multiline=True,
                    tooltip="System instructions for the LLM",
                ),
                io.String.Input(
                    "prompt",
                    default="",
                    multiline=True,
                    tooltip="User prompt to process",
                ),
                io.Int.Input(
                    "seed",
                    default=0,
                    min=0,
                    max=0xFFFFFFFFFFFFFFFF,
                    tooltip="Random seed for deterministic generation (if supported by model)",
                ),
            ],
            outputs=[io.String.Output(display_name="text")],
        )

    @classmethod
    def execute(cls, provider: Dict[str, Any], instructions: str, prompt: str, seed: int):
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

            if result is None:
                raise RuntimeError(
                    "LLM provider returned no text content (None). "
                    "This usually means the model response did not include a message body."
                )

            if not isinstance(result, str):
                raise RuntimeError(
                    f"LLM provider returned unsupported output type: {type(result).__name__}"
                )

            # Log successful generation (without sensitive data)
            model_info = provider.get("model_info", {})
            model_name = model_info.get("name", model_id)
            logging.info(f"LLM generation completed using {model_name}")

            if io is not None:
                return io.NodeOutput(result)
            return (result,)

        except Exception as e:
            if _is_processing_interrupt_exception(e):
                raise

            # Log error and re-raise for ComfyUI error handling
            logging.error(f"LLM Prompt Processor error: {str(e)}")
            raise RuntimeError(f"LLM processing failed: {str(e)}") from e

    def process_prompt(
        self, provider: Dict[str, Any], instructions: str, prompt: str, seed: int
    ) -> Tuple[str]:
        return self.__class__.execute(provider, instructions, prompt, seed)

    @classmethod
    def IS_CHANGED(cls, provider, instructions, prompt, seed):
        """Determine if node should be re-executed based on inputs."""
        # Always re-execute if any input changes
        return hash((str(provider), instructions, prompt, seed))

    @classmethod
    def fingerprint_inputs(cls, provider, instructions, prompt, seed):
        return hash((str(provider), instructions, prompt, seed))
