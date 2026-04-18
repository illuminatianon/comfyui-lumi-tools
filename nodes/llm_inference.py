"""
Base inference abstraction for LLM providers.
"""

import json
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Any, Optional

import requests

try:
    import comfy.model_management as model_management  # type: ignore[import-not-found]

    HAS_MODEL_MANAGEMENT = True
except ImportError:
    model_management = None
    HAS_MODEL_MANAGEMENT = False


def _throw_if_processing_interrupted() -> None:
    """Raise ComfyUI's interrupt exception when generation is cancelled."""
    if HAS_MODEL_MANAGEMENT and model_management is not None:
        model_management.throw_exception_if_processing_interrupted()


def _is_retryable_status(status_code: int) -> bool:
    return status_code == 408 or status_code == 425 or status_code == 429 or status_code >= 500


def _extract_error_message(response: requests.Response) -> str:
    try:
        error_body = response.json()
        return (
            error_body.get("error", {}).get("message")
            or error_body.get("message")
            or str(error_body)
        )
    except Exception:
        return response.text


def _normalize_message_content(content: Any) -> str | None:
    """Normalize OpenRouter message content into plain text when possible."""
    if content is None:
        return None

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                item_type = item.get("type")
                if item_type in {"text", "output_text"}:
                    text_value = item.get("text")
                    if isinstance(text_value, str):
                        text_parts.append(text_value)
            elif isinstance(item, str):
                text_parts.append(item)

        if text_parts:
            return "".join(text_parts)

    return None


def _extract_openrouter_text(result: dict[str, Any]) -> str:
    """Extract generated text from OpenRouter response with useful error context."""
    choices = result.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("No response choices received from OpenRouter")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise ValueError("Invalid OpenRouter response: first choice is not an object")

    message = first_choice.get("message")
    if not isinstance(message, dict):
        finish_reason = first_choice.get("finish_reason")
        raise ValueError(
            "Invalid OpenRouter response: missing message object "
            f"(finish_reason={finish_reason!r})"
        )

    normalized_content = _normalize_message_content(message.get("content"))
    if normalized_content is None:
        finish_reason = first_choice.get("finish_reason")
        refusal = message.get("refusal")
        raise ValueError(
            "OpenRouter returned empty/non-text message content "
            f"(finish_reason={finish_reason!r}, refusal={refusal!r})"
        )

    return normalized_content


def post_json_with_retries(
    url: str,
    *,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout: int,
    operation_name: str,
    max_attempts: int = 3,
    base_delay_seconds: float = 1.0,
) -> requests.Response:
    """POST JSON with retries for transient remote failures."""
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        _throw_if_processing_interrupted()

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            if response.ok:
                return response

            error_msg = _extract_error_message(response)
            if not _is_retryable_status(response.status_code) or attempt == max_attempts:
                raise RuntimeError(
                    f"{operation_name} API error ({response.status_code}): {error_msg}"
                )

            last_error = RuntimeError(
                f"{operation_name} API error ({response.status_code}): {error_msg}"
            )
        except requests.exceptions.RequestException as e:
            if attempt == max_attempts:
                raise RuntimeError(f"{operation_name} API request failed: {str(e)}") from e
            last_error = e

        if attempt < max_attempts:
            time.sleep(base_delay_seconds * (2 ** (attempt - 1)))

    if last_error is not None:
        raise RuntimeError(f"{operation_name} failed after {max_attempts} attempts") from last_error

    raise RuntimeError(f"{operation_name} failed after {max_attempts} attempts")


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

        _throw_if_processing_interrupted()

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
            response = self._post_with_interrupt_polling(headers=headers, payload=payload)
            _throw_if_processing_interrupted()
            response.raise_for_status()

            result = response.json()

            return _extract_openrouter_text(result)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"OpenRouter API request failed: {str(e)}") from e
        except (KeyError, IndexError) as e:
            raise ValueError(f"Invalid response format from OpenRouter: {str(e)}") from e
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse OpenRouter response: {str(e)}") from e

    def _post_with_interrupt_polling(
        self, headers: dict[str, str], payload: dict[str, Any]
    ) -> requests.Response:
        """Run the blocking request in a worker thread and poll for ComfyUI interrupts."""
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(
            post_json_with_retries,
            f"{self.base_url}/chat/completions",
            headers=headers,
            payload=payload,
            timeout=60,
            operation_name="OpenRouter",
        )

        try:
            while True:
                _throw_if_processing_interrupted()
                try:
                    return future.result(timeout=0.25)
                except TimeoutError:
                    continue
        finally:
            executor.shutdown(wait=False, cancel_futures=True)


def create_provider(provider_type: str, **kwargs) -> LLMProvider:
    """Factory function to create LLM providers."""
    if provider_type.lower() == "openrouter":
        return OpenRouterProvider(**kwargs)
    else:
        raise ValueError(f"Unsupported provider type: {provider_type}")
