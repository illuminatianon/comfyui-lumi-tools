"""
LLM Imagen Processor nodes for image generation via OpenRouter.

Contains:
- LumiGeminiImagenConfig: Configuration for Gemini imagen models
- LumiOpenRouterImagenProvider: Provider for OpenRouter imagen API
- LumiLLMImagenProcessor: Main processor that generates images
"""

import base64
import os
from io import BytesIO
from typing import Any, Dict, Tuple

import numpy as np
import requests
import torch
from PIL import Image

from .llm_inference import post_json_with_retries
from .v3_types import IMAGEN_CONFIG_TYPE, IMAGEN_PROVIDER_TYPE, LUMI_IMAGE_CHAIN_TYPE

try:
    from comfy_api.latest import io
except ImportError:
    io = None


_ComfyNodeBase = io.ComfyNode if io is not None else object

# Hardcoded list of Gemini imagen models available on OpenRouter
IMAGEN_MODELS_OPENROUTER = [
    {
        "id": "google/gemini-2.0-flash-preview-image-generation",
        "name": "Gemini 2.0 Flash Image",
        "family": "gemini",
        "max_resolution": "1K",
    },
    {
        "id": "google/gemini-3-pro-image-preview",
        "name": "Gemini 3.0 Image (Nano Banana Pro)",
        "family": "gemini",
        "max_resolution": "4K",
    },
    {
        "id": "google/gemini-3.1-flash-image-preview",
        "name": "Gemini 3.1 Flash Image Preview",
        "family": "gemini",
        "max_resolution": "4K",
    },
    {
        "id": "google/gemini-2.5-flash-image",
        "name": "Gemini 2.5 Flash Image (Nano Banana)",
        "family": "gemini",
        "max_resolution": "1K",
    },
]

# Hardcoded list of Gemini imagen models for direct Google AI Studio API
IMAGEN_MODELS_GOOGLE = [
    {
        "id": "gemini-3-pro-image-preview",
        "name": "Gemini 3.0 Image (Nano Banana Pro)",
        "family": "gemini",
        "max_resolution": "4K",
    },
    {
        "id": "gemini-3.1-flash-image-preview",
        "name": "Gemini 3.1 Flash Image Preview",
        "family": "gemini",
        "max_resolution": "4K",
    },
    {
        "id": "gemini-2.5-flash-image",
        "name": "Gemini 2.5 Flash Image (Nano Banana)",
        "family": "gemini",
        "max_resolution": "1K",
    },
]

# Supported aspect ratios for Gemini imagen
ASPECT_RATIOS = ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]

# Resolution options
RESOLUTIONS = ["1K", "2K", "4K"]


class LumiGeminiImagenConfig(_ComfyNodeBase):
    """Configuration node for Gemini imagen models."""

    @classmethod
    def INPUT_TYPES(cls):
        aspect_ratio_choices = tuple(ASPECT_RATIOS)
        resolution_choices = tuple(RESOLUTIONS)
        return {
            "required": {
                "aspect_ratio": (
                    aspect_ratio_choices,
                    {
                        "default": "16:9",
                        "tooltip": "Aspect ratio for generated images",
                    },
                ),
                "image_size": (
                    resolution_choices,
                    {
                        "default": "2K",
                        "tooltip": "Image size tier (1K, 2K, 4K). Note: gemini-2.0-flash only supports 1K",
                    },
                ),
                "temperature": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.0,
                        "max": 2.0,
                        "step": 0.05,
                        "tooltip": "Temperature for generation creativity",
                    },
                ),
                "top_p": (
                    "FLOAT",
                    {
                        "default": 1.0,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.01,
                        "tooltip": "Top-p sampling parameter",
                    },
                ),
            }
        }

    RETURN_TYPES = ("IMAGEN_CONFIG",)
    RETURN_NAMES = ("config",)
    FUNCTION = "execute"
    CATEGORY = "Lumi/LLM"

    DESCRIPTION = (
        "Creates configuration for Gemini imagen models. "
        "Configure aspect ratio, resolution, and generation parameters."
    )

    @staticmethod
    def _build_config(
        aspect_ratio: str,
        image_size: str,
        temperature: float,
        top_p: float,
    ) -> Dict[str, Any]:
        return {
            "config_type": "gemini",
            "aspect_ratio": aspect_ratio,
            "image_size": image_size,
            "temperature": temperature,
            "top_p": top_p,
        }

    @classmethod
    def define_schema(cls):
        if io is None or IMAGEN_CONFIG_TYPE is None:
            raise RuntimeError("ComfyUI V3 API is not available")

        return io.Schema(
            node_id="LumiGeminiImagenConfig",
            display_name="Lumi Gemini Imagen Config",
            category="Lumi/LLM",
            description=cls.DESCRIPTION,
            inputs=[
                io.Combo.Input(
                    "aspect_ratio",
                    options=tuple(ASPECT_RATIOS),
                    default="16:9",
                    tooltip="Aspect ratio for generated images",
                ),
                io.Combo.Input(
                    "image_size",
                    options=tuple(RESOLUTIONS),
                    default="2K",
                    tooltip="Image size tier (1K, 2K, 4K). Note: gemini-2.0-flash only supports 1K",
                ),
                io.Float.Input(
                    "temperature",
                    default=1.0,
                    min=0.0,
                    max=2.0,
                    step=0.05,
                    tooltip="Temperature for generation creativity",
                ),
                io.Float.Input(
                    "top_p",
                    default=1.0,
                    min=0.0,
                    max=1.0,
                    step=0.01,
                    tooltip="Top-p sampling parameter",
                ),
            ],
            outputs=[IMAGEN_CONFIG_TYPE.Output(display_name="config")],
        )

    @classmethod
    def execute(
        cls,
        aspect_ratio: str,
        image_size: str,
        temperature: float,
        top_p: float,
    ):
        """Create Gemini imagen configuration."""
        config = cls._build_config(aspect_ratio, image_size, temperature, top_p)
        if io is not None:
            return io.NodeOutput(config)
        return (config,)

    def create_config(
        self,
        aspect_ratio: str,
        image_size: str,
        temperature: float,
        top_p: float,
    ) -> Tuple[Dict[str, Any]]:
        return (self.__class__._build_config(aspect_ratio, image_size, temperature, top_p),)


class LumiOpenRouterImagenProvider(_ComfyNodeBase):
    """OpenRouter provider for imagen models."""

    @classmethod
    def INPUT_TYPES(cls):
        model_choices = [m["id"] for m in IMAGEN_MODELS_OPENROUTER]
        model_choices_tuple = tuple(model_choices)

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
                    model_choices_tuple,
                    {
                        "default": model_choices[0] if model_choices else "",
                        "tooltip": "Select the imagen model to use",
                    },
                ),
            }
        }

    RETURN_TYPES = ("IMAGEN_PROVIDER",)
    RETURN_NAMES = ("provider",)
    FUNCTION = "execute"
    CATEGORY = "Lumi/LLM"

    DESCRIPTION = (
        "Creates an OpenRouter provider for imagen models. "
        "The API key must be set as an environment variable."
    )

    @staticmethod
    def _build_provider_config(env_key: str, model: str) -> Dict[str, Any]:
        api_key = os.getenv(env_key.strip())
        if not api_key:
            raise ValueError(
                f"API key not found in environment variable '{env_key}'. "
                "Please set the environment variable with your OpenRouter API key."
            )

        model_info = next((m for m in IMAGEN_MODELS_OPENROUTER if m["id"] == model), None)
        if not model_info:
            model_info = {"id": model, "family": "gemini", "max_resolution": "1K"}

        return {
            "provider_type": "openrouter_imagen",
            "api_key": api_key,
            "model_id": model,
            "model_family": model_info.get("family", "gemini"),
            "max_resolution": model_info.get("max_resolution", "1K"),
            "env_key": env_key,
        }

    @classmethod
    def define_schema(cls):
        if io is None or IMAGEN_PROVIDER_TYPE is None:
            raise RuntimeError("ComfyUI V3 API is not available")

        model_choices = [m["id"] for m in IMAGEN_MODELS_OPENROUTER]

        return io.Schema(
            node_id="LumiOpenRouterImagenProvider",
            display_name="Lumi OpenRouter Imagen Provider",
            category="Lumi/LLM",
            description=cls.DESCRIPTION,
            inputs=[
                io.String.Input(
                    "env_key",
                    default="OPENROUTER_API_KEY",
                    tooltip="Environment variable name containing the OpenRouter API key",
                ),
                io.Combo.Input(
                    "model",
                    options=tuple(model_choices),
                    default=model_choices[0] if model_choices else "",
                    tooltip="Select the imagen model to use",
                ),
            ],
            outputs=[IMAGEN_PROVIDER_TYPE.Output(display_name="provider")],
        )

    @classmethod
    def execute(cls, env_key: str, model: str):
        """Create OpenRouter imagen provider configuration."""
        provider_config = cls._build_provider_config(env_key, model)
        if io is not None:
            return io.NodeOutput(provider_config)
        return (provider_config,)

    def create_provider(self, env_key: str, model: str) -> Tuple[Dict[str, Any]]:
        return (self.__class__._build_provider_config(env_key, model),)

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Always execute to prevent caching of API keys."""
        return float("nan")

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        return float("nan")

    def __getstate__(self):
        """Exclude sensitive data from workflow files."""
        return {"class_type": self.__class__.__name__, "version": "1.0"}


class LumiGoogleImagenProvider(_ComfyNodeBase):
    """Direct Google AI Studio provider for imagen models (faster than OpenRouter)."""

    @classmethod
    def INPUT_TYPES(cls):
        model_choices = [m["id"] for m in IMAGEN_MODELS_GOOGLE]
        model_choices_tuple = tuple(model_choices)

        return {
            "required": {
                "env_key": (
                    "STRING",
                    {
                        "default": "GOOGLE_API_KEY",
                        "tooltip": "Environment variable name containing the Google AI Studio API key",
                    },
                ),
                "model": (
                    model_choices_tuple,
                    {
                        "default": model_choices[0] if model_choices else "",
                        "tooltip": "Select the imagen model to use",
                    },
                ),
            }
        }

    RETURN_TYPES = ("IMAGEN_PROVIDER",)
    RETURN_NAMES = ("provider",)
    FUNCTION = "execute"
    CATEGORY = "Lumi/LLM"

    DESCRIPTION = (
        "Creates a direct Google AI Studio provider for imagen models. "
        "Faster than OpenRouter. API key must be set as an environment variable."
    )

    @staticmethod
    def _build_provider_config(env_key: str, model: str) -> Dict[str, Any]:
        api_key = os.getenv(env_key.strip())
        if not api_key:
            raise ValueError(
                f"API key not found in environment variable '{env_key}'. "
                "Please set the environment variable with your Google AI Studio API key."
            )

        model_info = next((m for m in IMAGEN_MODELS_GOOGLE if m["id"] == model), None)
        if not model_info:
            model_info = {"id": model, "family": "gemini", "max_resolution": "1K"}

        return {
            "provider_type": "google_imagen",
            "api_key": api_key,
            "model_id": model,
            "model_family": model_info.get("family", "gemini"),
            "max_resolution": model_info.get("max_resolution", "1K"),
            "env_key": env_key,
        }

    @classmethod
    def define_schema(cls):
        if io is None or IMAGEN_PROVIDER_TYPE is None:
            raise RuntimeError("ComfyUI V3 API is not available")

        model_choices = [m["id"] for m in IMAGEN_MODELS_GOOGLE]

        return io.Schema(
            node_id="LumiGoogleImagenProvider",
            display_name="Lumi Google Imagen Provider",
            category="Lumi/LLM",
            description=cls.DESCRIPTION,
            inputs=[
                io.String.Input(
                    "env_key",
                    default="GOOGLE_API_KEY",
                    tooltip="Environment variable name containing the Google AI Studio API key",
                ),
                io.Combo.Input(
                    "model",
                    options=tuple(model_choices),
                    default=model_choices[0] if model_choices else "",
                    tooltip="Select the imagen model to use",
                ),
            ],
            outputs=[IMAGEN_PROVIDER_TYPE.Output(display_name="provider")],
        )

    @classmethod
    def execute(cls, env_key: str, model: str):
        """Create Google AI Studio imagen provider configuration."""
        provider_config = cls._build_provider_config(env_key, model)
        if io is not None:
            return io.NodeOutput(provider_config)
        return (provider_config,)

    def create_provider(self, env_key: str, model: str) -> Tuple[Dict[str, Any]]:
        return (self.__class__._build_provider_config(env_key, model),)

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Always execute to prevent caching of API keys."""
        return float("nan")

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        return float("nan")

    def __getstate__(self):
        """Exclude sensitive data from workflow files."""
        return {"class_type": self.__class__.__name__, "version": "1.0"}


class LumiLLMImagenProcessor(_ComfyNodeBase):
    """Main imagen processor - generates images via OpenRouter API."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "provider": (
                    "IMAGEN_PROVIDER",
                    {"tooltip": "Imagen provider configuration"},
                ),
                "config": (
                    "IMAGEN_CONFIG",
                    {"tooltip": "Imagen generation configuration"},
                ),
                "prompt": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "tooltip": "User prompt describing the image to generate",
                    },
                ),
                "seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "tooltip": "Seed for generation (forces reprocessing)",
                    },
                ),
                "error_mode": (
                    ("fatal", "return_text", ""),
                    {
                        "default": "fatal",
                        "tooltip": "fatal: raise errors. return_text: return diagnostics in text output with a placeholder image.",
                    },
                ),
            },
            "optional": {
                "instructions": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "tooltip": "System instructions for the model (optional)",
                    },
                ),
                "input_images": (
                    "LUMI_IMAGE_CHAIN",
                    {
                        "tooltip": "Optional ordered image chain from Lumi Load Image nodes",
                    },
                ),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "text")
    FUNCTION = "execute"
    CATEGORY = "Lumi/LLM"

    DESCRIPTION = (
        "Generates images using Gemini imagen models. "
        "Supports both Google AI Studio (direct) and OpenRouter providers. "
        "Outputs images as a batch tensor and optional text response."
    )

    @classmethod
    def _generate_images_impl(
        cls,
        provider: Dict[str, Any],
        config: Dict[str, Any],
        prompt: str,
        seed: int,
        error_mode: str,
        instructions: str = "",
        input_images: Dict[str, Any] | None = None,
    ) -> Tuple[torch.Tensor, str]:
        processor = cls()
        normalized_error_mode = "return_text" if error_mode == "return_text" else "fatal"

        if provider.get("model_family") != config.get("config_type"):
            raise ValueError(
                f"Provider model family '{provider.get('model_family')}' "
                f"is not compatible with config type '{config.get('config_type')}'"
            )

        provider_type = provider.get("provider_type", "")
        image_data_urls = processor._extract_input_image_data_urls(input_images)

        if provider_type == "google_imagen":
            return processor._generate_google(
                provider,
                config,
                prompt,
                seed,
                normalized_error_mode,
                instructions,
                image_data_urls,
            )

        if provider_type == "openrouter_imagen":
            return processor._generate_openrouter(
                provider,
                config,
                prompt,
                seed,
                normalized_error_mode,
                instructions,
                image_data_urls,
            )

        raise ValueError(f"Unknown provider type: {provider_type}")

    @classmethod
    def define_schema(cls):
        if (
            io is None
            or IMAGEN_PROVIDER_TYPE is None
            or IMAGEN_CONFIG_TYPE is None
            or LUMI_IMAGE_CHAIN_TYPE is None
        ):
            raise RuntimeError("ComfyUI V3 API is not available")

        return io.Schema(
            node_id="LumiLLMImagenProcessor",
            display_name="Lumi LLM Imagen Processor",
            category="Lumi/LLM",
            description=cls.DESCRIPTION,
            inputs=[
                IMAGEN_PROVIDER_TYPE.Input("provider", tooltip="Imagen provider configuration"),
                IMAGEN_CONFIG_TYPE.Input("config", tooltip="Imagen generation configuration"),
                io.String.Input(
                    "prompt",
                    default="",
                    multiline=True,
                    tooltip="User prompt describing the image to generate",
                ),
                io.Int.Input(
                    "seed",
                    default=0,
                    min=0,
                    max=0xFFFFFFFFFFFFFFFF,
                    tooltip="Seed for generation (forces reprocessing)",
                ),
                io.Combo.Input(
                    "error_mode",
                    options=("fatal", "return_text", ""),
                    default="fatal",
                    tooltip="fatal: raise errors. return_text: return diagnostics in text output with a placeholder image.",
                ),
                io.String.Input(
                    "instructions",
                    default="",
                    multiline=True,
                    tooltip="System instructions for the model (optional)",
                    optional=True,
                ),
                LUMI_IMAGE_CHAIN_TYPE.Input(
                    "input_images",
                    tooltip="Optional ordered image chain from Lumi Load Image nodes",
                    optional=True,
                ),
            ],
            outputs=[
                io.Image.Output(display_name="images"),
                io.String.Output(display_name="text"),
            ],
        )

    @classmethod
    def execute(
        cls,
        provider: Dict[str, Any],
        config: Dict[str, Any],
        prompt: str,
        seed: int,
        error_mode: str,
        instructions: str = "",
        input_images: Dict[str, Any] | None = None,
    ):
        """Generate images using the configured provider and settings."""
        result = cls._generate_images_impl(
            provider,
            config,
            prompt,
            seed,
            error_mode,
            instructions=instructions,
            input_images=input_images,
        )

        if io is not None:
            return io.NodeOutput(*result)
        return result

    def generate_images(
        self,
        provider: Dict[str, Any],
        config: Dict[str, Any],
        prompt: str,
        seed: int,
        error_mode: str,
        instructions: str = "",
        input_images: Dict[str, Any] | None = None,
    ) -> Tuple[torch.Tensor, str]:
        return self.__class__._generate_images_impl(
            provider,
            config,
            prompt,
            seed,
            error_mode,
            instructions=instructions,
            input_images=input_images,
        )

    def _generate_google(
        self,
        provider: Dict[str, Any],
        config: Dict[str, Any],
        prompt: str,
        seed: int,
        error_mode: str,
        instructions: str,
        input_image_data_urls: list[str],
    ) -> Tuple[torch.Tensor, str]:
        """Generate images via direct Google AI Studio API."""
        # Build prompt text
        full_prompt = prompt.strip()
        if instructions.strip():
            full_prompt = f"{instructions.strip()}\n\n{full_prompt}"

        parts: list[Dict[str, Any]] = [{"text": full_prompt}]
        for data_url in input_image_data_urls:
            b64_data = data_url.split(",", maxsplit=1)[1] if "," in data_url else data_url
            parts.append(
                {
                    "inlineData": {
                        "mimeType": "image/png",
                        "data": b64_data,
                    }
                }
            )

        # Build payload for Google API
        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "responseModalities": ["Image", "Text"],
                "temperature": config.get("temperature", 1.0),
                "topP": config.get("top_p", 1.0),
                "imageConfig": {
                    "aspectRatio": config.get("aspect_ratio", "1:1"),
                },
            },
        }

        # Add imageSize only for models that support higher resolutions
        # gemini-2.5-flash only supports 1K, gemini-3.x image preview models support up to 4K
        image_size = config.get("image_size", "1K")
        max_resolution = provider.get("max_resolution", "1K")
        resolution_order = ["1K", "2K", "4K"]
        max_idx = (
            resolution_order.index(max_resolution) if max_resolution in resolution_order else 0
        )
        req_idx = resolution_order.index(image_size) if image_size in resolution_order else 0
        # Cap to model's max resolution
        effective_size = resolution_order[min(req_idx, max_idx)]
        if effective_size != "1K":
            payload["generationConfig"]["imageConfig"]["imageSize"] = effective_size

        # Add seed (capped to INT32 max)
        if seed is not None:
            payload["generationConfig"]["seed"] = seed % 2147483647

        # Build URL with model and API key
        model_id = provider["model_id"]
        api_key = provider["api_key"]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent"

        headers = {
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        }

        try:
            response = post_json_with_retries(
                url,
                headers=headers,
                payload=payload,
                timeout=120,
                operation_name="Google",
            )
            result = response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Google API request failed: {str(e)}") from e

        # Extract response - Google format has parts with text and inlineData
        try:
            parts = result["candidates"][0]["content"]["parts"]
        except (KeyError, IndexError) as e:
            diagnostics = self._extract_google_diagnostics(result)
            message = f"Invalid response format from Google API: {str(e)}"
            if diagnostics:
                message = f"{message}. {diagnostics}"
            if error_mode == "return_text":
                return (self._empty_image_tensor(), message)
            raise ValueError(message) from e

        text_response = ""
        image_data = None

        for part in parts:
            if "text" in part:
                text_response = part["text"]
            elif "inlineData" in part:
                image_data = part["inlineData"]["data"]

        if not image_data:
            diagnostics = self._extract_google_diagnostics(result)
            message = "No image returned from Google API"
            if diagnostics:
                message = f"{message}. {diagnostics}"
            if error_mode == "return_text":
                output_text = message
                if text_response:
                    output_text = f"{output_text}\n\nModel text:\n{text_response}"
                return (self._empty_image_tensor(), output_text)
            raise ValueError(message)

        # Convert to tensor
        tensor = self._decode_image(image_data)

        return (tensor, text_response)

    def _generate_openrouter(
        self,
        provider: Dict[str, Any],
        config: Dict[str, Any],
        prompt: str,
        seed: int,
        error_mode: str,
        instructions: str,
        input_image_data_urls: list[str],
    ) -> Tuple[torch.Tensor, str]:
        """Generate images via OpenRouter API."""
        # Build messages
        messages = []
        if instructions.strip():
            messages.append({"role": "system", "content": instructions.strip()})

        if input_image_data_urls:
            user_content: list[Dict[str, Any]] = [{"type": "text", "text": prompt.strip()}]
            for data_url in input_image_data_urls:
                user_content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": data_url},
                    }
                )
            messages.append({"role": "user", "content": user_content})
        else:
            messages.append({"role": "user", "content": prompt.strip()})

        # Build payload
        payload = {
            "model": provider["model_id"],
            "messages": messages,
            "modalities": ["image", "text"],
            "temperature": config.get("temperature", 1.0),
            "top_p": config.get("top_p", 1.0),
            "image_config": {
                "aspect_ratio": config.get("aspect_ratio", "1:1"),
                "image_size": config.get("image_size", "1K"),
            },
        }

        # Add seed (capped to INT32 max for Google API compatibility)
        if seed is not None:
            payload["seed"] = seed % 2147483647

        headers = {
            "Authorization": f"Bearer {provider['api_key']}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/illuminatianon/comfyui-lumi-tools",
            "X-Title": "ComfyUI Lumi Tools",
        }

        try:
            response = post_json_with_retries(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                payload=payload,
                timeout=180,
                operation_name="OpenRouter imagen",
            )
            result = response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"OpenRouter API request failed: {str(e)}") from e

        # Extract response
        try:
            choice = result["choices"][0]["message"]
            text_response = choice.get("content", "") or ""
            images_data = choice.get("images", [])
        except (KeyError, IndexError) as e:
            message = f"Invalid response format from OpenRouter: {str(e)}"
            if error_mode == "return_text":
                return (self._empty_image_tensor(), message)
            raise ValueError(message) from e

        if not images_data:
            message = "No images returned from OpenRouter API"
            if error_mode == "return_text":
                output_text = message
                if text_response:
                    output_text = f"{output_text}\n\nModel text:\n{text_response}"
                return (self._empty_image_tensor(), output_text)
            raise ValueError(message)

        # Get first image URL
        first_image = images_data[0]
        url = first_image.get("image_url", {}).get("url", "")
        if not url:
            raise ValueError("No valid image URL in response")

        # Convert to tensor
        tensor = self._decode_image(url)

        return (tensor, text_response)

    def _decode_image(self, url: str) -> torch.Tensor:
        """Convert base64 data URL to ComfyUI image tensor."""
        # Strip data URL prefix if present
        b64_data = url.split(",")[1] if "," in url else url
        image_bytes = base64.b64decode(b64_data)
        pil_image = Image.open(BytesIO(image_bytes)).convert("RGB")
        np_image = np.array(pil_image).astype(np.float32) / 255.0
        return torch.from_numpy(np_image).unsqueeze(0)  # (1, H, W, C)

    def _extract_input_image_data_urls(self, input_images: Dict[str, Any] | None) -> list[str]:
        """Extract ordered input images and encode them as PNG data URLs."""
        if not input_images or not isinstance(input_images, dict):
            return []

        chain = input_images.get("images", [])
        if not isinstance(chain, list):
            return []

        data_urls: list[str] = []
        for item in chain:
            if not isinstance(item, torch.Tensor):
                continue

            if item.ndim == 4:
                tensors = [item[i] for i in range(item.shape[0])]
            elif item.ndim == 3:
                tensors = [item]
            else:
                continue

            for tensor in tensors:
                data_urls.append(self._encode_tensor_to_data_url(tensor))

        return data_urls

    def _encode_tensor_to_data_url(self, image_tensor: torch.Tensor) -> str:
        """Encode a ComfyUI image tensor as a PNG data URL."""
        np_image = image_tensor.cpu().numpy()
        np_image = np.clip(np_image, 0.0, 1.0)
        np_image = (np_image * 255.0).astype(np.uint8)

        pil_image = Image.fromarray(np_image)
        output = BytesIO()
        pil_image.save(output, format="PNG")
        b64_data = base64.b64encode(output.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{b64_data}"

    def _empty_image_tensor(self) -> torch.Tensor:
        """Return a 1x1 black placeholder image tensor."""
        return torch.zeros((1, 1, 1, 3), dtype=torch.float32)

    def _extract_google_diagnostics(self, result: Dict[str, Any]) -> str:
        """Extract helpful moderation and finish diagnostics from Google responses."""
        diagnostics: list[str] = []

        prompt_feedback = result.get("promptFeedback", {}) if isinstance(result, dict) else {}
        if isinstance(prompt_feedback, dict):
            block_reason = prompt_feedback.get("blockReason")
            if block_reason:
                diagnostics.append(f"blockReason={block_reason}")

            safety_ratings = prompt_feedback.get("safetyRatings", [])
            if isinstance(safety_ratings, list) and safety_ratings:
                categories = [
                    f"{r.get('category')}:{r.get('probability')}"
                    for r in safety_ratings
                    if isinstance(r, dict)
                ]
                categories = [c for c in categories if c]
                if categories:
                    diagnostics.append(f"promptSafety={', '.join(categories)}")

        candidates = result.get("candidates", []) if isinstance(result, dict) else []
        if isinstance(candidates, list) and candidates:
            finish_reason = (
                candidates[0].get("finishReason") if isinstance(candidates[0], dict) else None
            )
            if finish_reason:
                diagnostics.append(f"finishReason={finish_reason}")

            candidate_safety = (
                candidates[0].get("safetyRatings", []) if isinstance(candidates[0], dict) else []
            )
            if isinstance(candidate_safety, list) and candidate_safety:
                categories = [
                    f"{r.get('category')}:{r.get('probability')}"
                    for r in candidate_safety
                    if isinstance(r, dict)
                ]
                categories = [c for c in categories if c]
                if categories:
                    diagnostics.append(f"candidateSafety={', '.join(categories)}")

        return "; ".join(diagnostics)
