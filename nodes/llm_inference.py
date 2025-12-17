"""
Base inference abstraction for LLM providers.
"""

import json
from abc import ABC, abstractmethod
from typing import Optional

import requests


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, api_key: str, model_id: str, max_tokens: int = 1000, top_p: float = 1.0):
        self.api_key = api_key
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.top_p = top_p

    @abstractmethod
    def generate(self, instructions: str, prompt: str, seed: Optional[int] = None) -> str:
        """Generate text using the LLM provider."""
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """Validate the provider configuration."""
        pass


class OpenRouterProvider(LLMProvider):
    """OpenRouter LLM provider implementation."""

    def __init__(self, api_key: str, model_id: str, max_tokens: int = 1000, top_p: float = 1.0):
        super().__init__(api_key, model_id, max_tokens, top_p)
        self.base_url = "https://openrouter.ai/api/v1"

    def validate_config(self) -> bool:
        """Validate OpenRouter configuration."""
        if not self.api_key:
            return False
        if not self.model_id:
            return False
        return True

    def generate(self, instructions: str, prompt: str, seed: Optional[int] = None) -> str:
        """Generate text using OpenRouter API."""
        if not self.validate_config():
            raise ValueError("Invalid OpenRouter configuration")

        # Combine instructions and prompt
        messages = []
        if instructions.strip():
            messages.append({"role": "system", "content": instructions.strip()})
        messages.append({"role": "user", "content": prompt.strip()})

        # Prepare request payload
        payload = {
            "model": self.model_id,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        }

        # Add seed if provided and supported
        if seed is not None:
            payload["seed"] = seed

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/illuminatianon/comfyui-lumi-tools",
            "X-Title": "ComfyUI Lumi Tools",
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=60
            )
            response.raise_for_status()

            result = response.json()

            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                raise ValueError("No response content received from OpenRouter")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"OpenRouter API request failed: {str(e)}") from e
        except (KeyError, IndexError) as e:
            raise ValueError(f"Invalid response format from OpenRouter: {str(e)}") from e
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse OpenRouter response: {str(e)}") from e


def create_provider(provider_type: str, **kwargs) -> LLMProvider:
    """Factory function to create LLM providers."""
    if provider_type.lower() == "openrouter":
        return OpenRouterProvider(**kwargs)
    else:
        raise ValueError(f"Unsupported provider type: {provider_type}")
