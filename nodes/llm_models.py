"""
Model caching and management for LLM providers.
"""

import logging
from typing import Dict, List, Optional

import requests


class ModelCache:
    """Manages caching of LLM models from various providers."""

    def __init__(self):
        self._models: Dict[str, List[Dict]] = {}
        self._initialized = False

    def initialize(self):
        """Initialize model cache by fetching from providers."""
        if self._initialized:
            return

        self._fetch_openrouter_models()
        self._initialized = True

    def _fetch_openrouter_models(self):
        """Fetch models from OpenRouter API with fallback."""
        try:
            response = requests.get("https://openrouter.ai/api/v1/models", timeout=10)
            response.raise_for_status()

            models_data = response.json()
            if "data" in models_data:
                self._models["openrouter"] = models_data["data"]
                logging.info(f"Cached {len(models_data['data'])} OpenRouter models")
            else:
                self._use_fallback_models()
        except Exception as e:
            logging.warning(f"Failed to fetch OpenRouter models: {e}")
            self._use_fallback_models()

    def _use_fallback_models(self):
        """Use fallback list of common OpenRouter models."""
        fallback_models = [
            {
                "id": "openai/gpt-4o",
                "name": "OpenAI: GPT-4o",
                "context_length": 128000,
                "pricing": {"prompt": "0.000005", "completion": "0.000015"},
            },
            {
                "id": "openai/gpt-4o-mini",
                "name": "OpenAI: GPT-4o Mini",
                "context_length": 128000,
                "pricing": {"prompt": "0.00000015", "completion": "0.0000006"},
            },
            {
                "id": "anthropic/claude-3.5-sonnet",
                "name": "Anthropic: Claude 3.5 Sonnet",
                "context_length": 200000,
                "pricing": {"prompt": "0.000003", "completion": "0.000015"},
            },
            {
                "id": "google/gemini-pro-1.5",
                "name": "Google: Gemini Pro 1.5",
                "context_length": 2000000,
                "pricing": {"prompt": "0.00000125", "completion": "0.000005"},
            },
        ]
        self._models["openrouter"] = fallback_models
        logging.info(f"Using fallback models: {len(fallback_models)} models")

    def get_models(self, provider: str = "openrouter") -> List[Dict]:
        """Get cached models for a provider."""
        if not self._initialized:
            self.initialize()
        return self._models.get(provider, [])

    def get_model_by_id(self, model_id: str, provider: str = "openrouter") -> Optional[Dict]:
        """Get a specific model by ID."""
        models = self.get_models(provider)
        for model in models:
            if model.get("id") == model_id:
                return model
        return None

    def get_model_choices(self, provider: str = "openrouter") -> List[str]:
        """Get list of model IDs for UI dropdown."""
        models = self.get_models(provider)
        return [model.get("id", "") for model in models if model.get("id")]


# Global model cache instance
model_cache = ModelCache()
