# LLM Imagen Processor Design

## Status: ✅ Complete

## Overview

Image generation system using Gemini imagen models via direct Google AI Studio API or OpenRouter. Follows similar pattern to LLMPromptProcessor but with model-specific config nodes.

**Key Design Principles:**
- Provider node is separate from processor (same pattern as text LLM)
- API keys managed via environment variables (never exposed in UI or workflow files)
- Processor is stateless - provider node manages configuration
- Inference via REST APIs using `requests` (no provider-specific libraries)
- Fail fast on errors - no retry logic, failures take down the job

**Supported Providers:**
- **Google AI Studio (Direct)** - Recommended, ~4x faster than OpenRouter
- **OpenRouter** - Alternative, supports same Gemini models

## Architecture

```
[LumiGoogleImagenProvider] ──────┐
       OR                        ├──► [LumiLLMImagenProcessor] ──► IMAGE
[LumiOpenRouterImagenProvider] ──┤                            └──► STRING (text)
                                 │
[LumiGeminiImagenConfig] ────────┘
         ▲
    instructions (STRING, forceInput, optional)
    prompt (STRING, forceInput)
    seed (INT)
```

## Nodes

### 1. LumiOpenRouterImagenProvider

Extends/filters OpenRouter for image-capable models only.

**Inputs:**
- `env_key`: STRING (default: "OPENROUTER_API_KEY")
- `model`: Dropdown of imagen-capable models (hardcoded list initially)

**Outputs:**
- `IMAGEN_PROVIDER` (provider config dict)

**Provider Config Dict Structure:**
```python
{
    "provider_type": "openrouter_imagen",
    "api_key": api_key,          # From env var, not serialized
    "model_id": model,           # Full OpenRouter model ID
    "model_family": "gemini",    # For config compatibility checking
    "env_key": env_key,          # Store for reference
}
```

**Supported Models (hardcoded to start):**
```python
IMAGEN_MODELS = [
    {
        "id": "google/gemini-2.0-flash-preview-image-generation",
        "name": "Gemini 2.0 Flash Image",
        "family": "gemini",
        "max_resolution": "1K",
    },
    # Add more as they become available on OpenRouter
]
```

**Notes:**
- Reuses same API key mechanism as LumiOpenRouterProvider
- `IS_CHANGED` returns `float("nan")` to prevent caching of API keys
- Custom `__getstate__` to exclude sensitive data from workflow files

---

### 2. LumiGeminiImagenConfig

Config node specific to Gemini imagen models.

**Inputs:**
- `temperature`: FLOAT (0.0-2.0, default 1.0)
- `top_p`: FLOAT (0.0-1.0, default 1.0)
- `aspect_ratio`: Dropdown (see table below)
- `resolution`: Dropdown ["1K", "2K", "4K"] (only for gemini-3-pro; ignored for flash)
- `num_images`: INT (1-4, default 1) - batch generation

**Supported Aspect Ratios** (confirmed from Google docs):
```python
ASPECT_RATIOS = ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]
```

**Outputs:**
- `IMAGEN_CONFIG` (config dict)

**Config Dict Structure:**
```python
{
    "config_type": "gemini",     # For compatibility checking
    "temperature": temperature,
    "top_p": top_p,
    "aspect_ratio": aspect_ratio,
    "resolution": resolution,
    "num_images": num_images,
}
```

**Resolution Details (from Google docs):**

| Aspect | 1K | 2K | 4K |
|--------|-----|------|------|
| 1:1 | 1024x1024 | 2048x2048 | 4096x4096 |
| 2:3 | 832x1248 | 1664x2496 | 3328x4992 |
| 3:2 | 1248x832 | 2496x1664 | 4992x3328 |
| 3:4 | 896x1152 | 1792x2304 | 3584x4608 |
| 4:3 | 1152x896 | 2304x1792 | 4608x3584 |
| 4:5 | 896x1152 | 1792x2304 | 3584x4608 |
| 5:4 | 1152x896 | 2304x1792 | 4608x3584 |
| 9:16 | 768x1376 | 1536x2752 | 3072x5504 |
| 16:9 | 1376x768 | 2752x1536 | 5504x3072 |
| 21:9 | 1536x640 | 3072x1280 | 6144x2560 |

**Notes:**
- Config is passed through to API's `image_config` field
- `gemini-2.0-flash` only supports 1K resolution - higher resolutions will be ignored/downgraded

---

### 3. LumiLLMImagenProcessor

Main inference node - stateless, makes API call and converts response to IMAGE.

**Inputs:**
- `provider`: IMAGEN_PROVIDER (from provider node)
- `config`: IMAGEN_CONFIG (from config node)
- `instructions`: STRING (forceInput) - system prompt
- `prompt`: STRING (forceInput) - user prompt
- `seed`: INT (widget with input option)

**Outputs:**
- `IMAGE` - ComfyUI image tensor (B, H, W, C) float32 0-1
- `text` - STRING, optional text response from the model

**Compatibility Validation:**
- Check `provider["model_family"]` matches `config["config_type"]`
- If incompatible, raise `ValueError` with helpful message

**Notes:**
- If provider/config incompatible, error and abort
- Converts base64 response to tensor
- Multiple images stacked into batch dimension

---

## OpenRouter API Details

### Request Format
```python
payload = {
    "model": "google/gemini-2.0-flash-preview-image-generation",
    "messages": [
        {"role": "system", "content": instructions},
        {"role": "user", "content": prompt}
    ],
    "modalities": ["image", "text"],
    "temperature": config["temperature"],
    "top_p": config["top_p"],
    "image_config": {
        "aspect_ratio": config["aspect_ratio"],
        "resolution": config["resolution"],
        "num_images": config["num_images"],
    }
}

# Add seed if provided
if seed is not None:
    payload["seed"] = seed
```

### Request Headers
```python
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/illuminatianon/comfyui-lumi-tools",
    "X-Title": "ComfyUI Lumi Tools",
}
```

### Response Format
```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "optional text response",
      "images": [{
        "type": "image_url",
        "image_url": {
          "url": "data:image/png;base64,iVBORw0KGgo..."
        }
      }]
    }
  }]
}
```

### Image Conversion (base64 → ComfyUI tensor)
```python
import base64
import numpy as np
from PIL import Image
from io import BytesIO
import torch

def decode_image(url: str) -> torch.Tensor:
    """Convert base64 data URL to ComfyUI image tensor."""
    # Strip data URL prefix if present
    b64_data = url.split(",")[1] if "," in url else url
    image_bytes = base64.b64decode(b64_data)
    pil_image = Image.open(BytesIO(image_bytes)).convert("RGB")
    np_image = np.array(pil_image).astype(np.float32) / 255.0
    return torch.from_numpy(np_image).unsqueeze(0)  # (1, H, W, C)

# For multiple images, stack into batch:
tensors = [decode_image(img["image_url"]["url"]) for img in images]
batch = torch.cat(tensors, dim=0)  # (B, H, W, C)
```

### Timeout
- Use 120 seconds (image generation is slower than text)

---

## Error Handling

Fail fast - no retry logic. If API fails, the job fails.

```python
try:
    response = requests.post(url, headers=headers, json=payload, timeout=120)
    response.raise_for_status()
    result = response.json()
    # ... process response
except requests.exceptions.RequestException as e:
    raise RuntimeError(f"OpenRouter API request failed: {str(e)}") from e
except (KeyError, IndexError) as e:
    raise ValueError(f"Invalid response format from OpenRouter: {str(e)}") from e
```

---

## Decisions Log

1. **Model list**: Hardcoded Gemini models only for now

2. **Multiple images**: Stack into batch tensor (B, H, W, C) - ComfyUI handles this natively

3. **Seed support**: Send seed to API anyway (forces ComfyUI reprocessing, API will ignore if unsupported)

4. **Resolution**: Values are "1K", "2K", "4K" - only higher-tier models support 2K/4K

5. **Text output**: Output optional text response as second output (useful when model describes what it generated)

6. **Error handling**: Fail fast, no retries - if you hit rate limits or errors, that's on you

---

## File Organization

All imagen nodes in `nodes/llm_imagen_processor.py`:
- `LumiGeminiImagenConfig`
- `LumiOpenRouterImagenProvider`
- `LumiLLMImagenProcessor`

Can split later if needed.

---

## Implementation Order

1. [x] Create `llm_imagen_processor.py` with all three nodes
2. [x] Register nodes in `__init__.py`
3. [x] Test end-to-end
4. [x] Add direct Google AI Studio provider (LumiGoogleImagenProvider) - ~4x faster than OpenRouter

