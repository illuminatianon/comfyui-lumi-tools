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


class LumiGeminiImagenConfig:
    """Configuration node for Gemini imagen models."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "aspect_ratio": (
                    ASPECT_RATIOS,
                    {
                        "default": "16:9",
                        "tooltip": "Aspect ratio for generated images",
                    },
                ),
                "image_size": (
                    RESOLUTIONS,
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
    FUNCTION = "create_config"
    CATEGORY = "Lumi/LLM"

    DESCRIPTION = (
        "Creates configuration for Gemini imagen models. "
        "Configure aspect ratio, resolution, and generation parameters."
    )

    def create_config(
        self,
        aspect_ratio: str,
        image_size: str,
        temperature: float,
        top_p: float,
    ) -> Tuple[Dict[str, Any]]:
        """Create Gemini imagen configuration."""
        config = {
            "config_type": "gemini",
            "aspect_ratio": aspect_ratio,
            "image_size": image_size,
            "temperature": temperature,
            "top_p": top_p,
        }
        return (config,)


class LumiOpenRouterImagenProvider:
    """OpenRouter provider for imagen models."""

    @classmethod
    def INPUT_TYPES(cls):
        model_choices = [m["id"] for m in IMAGEN_MODELS_OPENROUTER]

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
                        "default": model_choices[0] if model_choices else "",
                        "tooltip": "Select the imagen model to use",
                    },
                ),
            }
        }

    RETURN_TYPES = ("IMAGEN_PROVIDER",)
    RETURN_NAMES = ("provider",)
    FUNCTION = "create_provider"
    CATEGORY = "Lumi/LLM"

    DESCRIPTION = (
        "Creates an OpenRouter provider for imagen models. "
        "The API key must be set as an environment variable."
    )

    def create_provider(self, env_key: str, model: str) -> Tuple[Dict[str, Any]]:
        """Create OpenRouter imagen provider configuration."""
        # Get API key from environment
        api_key = os.getenv(env_key.strip())
        if not api_key:
            raise ValueError(
                f"API key not found in environment variable '{env_key}'. "
                f"Please set the environment variable with your OpenRouter API key."
            )

        # Find model info
        model_info = next((m for m in IMAGEN_MODELS_OPENROUTER if m["id"] == model), None)
        if not model_info:
            model_info = {"id": model, "family": "gemini", "max_resolution": "1K"}

        provider_config = {
            "provider_type": "openrouter_imagen",
            "api_key": api_key,
            "model_id": model,
            "model_family": model_info.get("family", "gemini"),
            "max_resolution": model_info.get("max_resolution", "1K"),
            "env_key": env_key,
        }
        return (provider_config,)

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Always execute to prevent caching of API keys."""
        return float("nan")

    def __getstate__(self):
        """Exclude sensitive data from workflow files."""
        return {"class_type": self.__class__.__name__, "version": "1.0"}


class LumiGoogleImagenProvider:
    """Direct Google AI Studio provider for imagen models (faster than OpenRouter)."""

    @classmethod
    def INPUT_TYPES(cls):
        model_choices = [m["id"] for m in IMAGEN_MODELS_GOOGLE]

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
                    model_choices,
                    {
                        "default": model_choices[0] if model_choices else "",
                        "tooltip": "Select the imagen model to use",
                    },
                ),
            }
        }

    RETURN_TYPES = ("IMAGEN_PROVIDER",)
    RETURN_NAMES = ("provider",)
    FUNCTION = "create_provider"
    CATEGORY = "Lumi/LLM"

    DESCRIPTION = (
        "Creates a direct Google AI Studio provider for imagen models. "
        "Faster than OpenRouter. API key must be set as an environment variable."
    )

    def create_provider(self, env_key: str, model: str) -> Tuple[Dict[str, Any]]:
        """Create Google AI Studio imagen provider configuration."""
        # Get API key from environment
        api_key = os.getenv(env_key.strip())
        if not api_key:
            raise ValueError(
                f"API key not found in environment variable '{env_key}'. "
                f"Please set the environment variable with your Google AI Studio API key."
            )

        # Find model info
        model_info = next((m for m in IMAGEN_MODELS_GOOGLE if m["id"] == model), None)
        if not model_info:
            model_info = {"id": model, "family": "gemini", "max_resolution": "1K"}

        provider_config = {
            "provider_type": "google_imagen",
            "api_key": api_key,
            "model_id": model,
            "model_family": model_info.get("family", "gemini"),
            "max_resolution": model_info.get("max_resolution", "1K"),
            "env_key": env_key,
        }
        return (provider_config,)

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Always execute to prevent caching of API keys."""
        return float("nan")

    def __getstate__(self):
        """Exclude sensitive data from workflow files."""
        return {"class_type": self.__class__.__name__, "version": "1.0"}


class LumiLLMImagenProcessor:
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
                        "forceInput": True,
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
            },
            "optional": {
                "instructions": (
                    "STRING",
                    {
                        "forceInput": True,
                        "tooltip": "System instructions for the model (optional)",
                    },
                ),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "text")
    FUNCTION = "generate_images"
    CATEGORY = "Lumi/LLM"

    DESCRIPTION = (
        "Generates images using Gemini imagen models. "
        "Supports both Google AI Studio (direct) and OpenRouter providers. "
        "Outputs images as a batch tensor and optional text response."
    )

    def generate_images(
        self,
        provider: Dict[str, Any],
        config: Dict[str, Any],
        prompt: str,
        seed: int,
        instructions: str = "",
    ) -> Tuple[torch.Tensor, str]:
        """Generate images using the configured provider and settings."""
        # Validate compatibility
        if provider.get("model_family") != config.get("config_type"):
            raise ValueError(
                f"Provider model family '{provider.get('model_family')}' "
                f"is not compatible with config type '{config.get('config_type')}'"
            )

        # Route to appropriate provider
        provider_type = provider.get("provider_type", "")
        if provider_type == "google_imagen":
            return self._generate_google(provider, config, prompt, seed, instructions)
        elif provider_type == "openrouter_imagen":
            return self._generate_openrouter(provider, config, prompt, seed, instructions)
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")

    def _generate_google(
        self,
        provider: Dict[str, Any],
        config: Dict[str, Any],
        prompt: str,
        seed: int,
        instructions: str,
    ) -> Tuple[torch.Tensor, str]:
        """Generate images via direct Google AI Studio API."""
        # Build prompt text
        full_prompt = prompt.strip()
        if instructions.strip():
            full_prompt = f"{instructions.strip()}\n\n{full_prompt}"

        # Build payload for Google API
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
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
        # gemini-2.5-flash only supports 1K, gemini-3-pro supports up to 4K
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

        # Make API request
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            if not response.ok:
                try:
                    error_body = response.json()
                    error_msg = (
                        error_body.get("error", {}).get("message")
                        or error_body.get("message")
                        or str(error_body)
                    )
                except Exception:
                    error_msg = response.text
                raise RuntimeError(f"Google API error ({response.status_code}): {error_msg}")
            result = response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Google API request failed: {str(e)}") from e

        # Extract response - Google format has parts with text and inlineData
        try:
            parts = result["candidates"][0]["content"]["parts"]
        except (KeyError, IndexError) as e:
            raise ValueError(f"Invalid response format from Google API: {str(e)}") from e

        text_response = ""
        image_data = None

        for part in parts:
            if "text" in part:
                text_response = part["text"]
            elif "inlineData" in part:
                image_data = part["inlineData"]["data"]

        if not image_data:
            raise ValueError("No image returned from Google API")

        # Convert to tensor
        tensor = self._decode_image(image_data)

        return (tensor, text_response)

    def _generate_openrouter(
        self,
        provider: Dict[str, Any],
        config: Dict[str, Any],
        prompt: str,
        seed: int,
        instructions: str,
    ) -> Tuple[torch.Tensor, str]:
        """Generate images via OpenRouter API."""
        # Build messages
        messages = []
        if instructions.strip():
            messages.append({"role": "system", "content": instructions.strip()})
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

        # Make API request
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=180,
            )
            if not response.ok:
                try:
                    error_body = response.json()
                    error_msg = (
                        error_body.get("error", {}).get("message")
                        or error_body.get("message")
                        or str(error_body)
                    )
                except Exception:
                    error_msg = response.text
                raise RuntimeError(f"OpenRouter API error ({response.status_code}): {error_msg}")
            result = response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"OpenRouter API request failed: {str(e)}") from e

        # Extract response
        try:
            choice = result["choices"][0]["message"]
            text_response = choice.get("content", "") or ""
            images_data = choice.get("images", [])
        except (KeyError, IndexError) as e:
            raise ValueError(f"Invalid response format from OpenRouter: {str(e)}") from e

        if not images_data:
            raise ValueError("No images returned from OpenRouter API")

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
