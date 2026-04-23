# Lumi Tools

A collection of utility nodes for ComfyUI.

## Installation

1. Clone or symlink this repository into your ComfyUI `custom_nodes` folder
2. Install dependencies:
   ```bash
   uv sync
   ```
3. Restart ComfyUI

### Development Setup

```bash
uv sync --dev
```

## Nodes

All nodes appear under **Lumi/** in the node menu.

### Prompt & Text Nodes

#### Lumi Shuffle Prompt

Shuffles tokens in a prompt string. Useful for randomizing tag order.

- Strips newlines and commas
- Splits by spaces, shuffles, and rejoins
- Seeded for reproducibility

#### Lumi Wildcard Processor

Processes wildcard prompts using [dynamicprompts](https://github.com/adieyal/dynamicprompts).

#### Lumi Wrap Text

Wraps text with optional prefix and suffix strings.

#### Lumi Text Input

Provides an arbitrary multiline text input.

#### Lumi Show Text

Displays text output for debugging.

### LLM Nodes

#### Lumi OpenRouter Provider

Provides OpenRouter API configuration for LLM inference. Requires `OPENROUTER_API_KEY` environment variable.

#### Lumi LLM Prompt Processor

Processes prompts using LLM inference via OpenRouter. Useful for prompt enhancement and rewriting.

### Image Generation Nodes

#### Lumi LLM Imagen Config

Combined configuration node for image generation models. Selects the config family and dynamically shows the relevant generation settings.

For Gemini configs, it sets aspect ratio (default: 16:9), image size (default: 2K), temperature, and top-p.

#### Lumi LLM Imagen Provider

Combined provider node for image generation APIs. Select `google` or `openrouter` and the node dynamically shows the matching API key environment variable and model list.

Google AI Studio uses `GOOGLE_API_KEY` and is much faster than OpenRouter (~4x). OpenRouter uses `OPENROUTER_API_KEY`.

Available models:
- `gemini-3-pro-image-preview` (default, supports up to 4K)
- `gemini-3.1-flash-image-preview` (supports up to 4K)
- `gemini-2.5-flash-image` (1K only)
- `google/gemini-2.0-flash-preview-image-generation` (OpenRouter only, 1K only)

#### Lumi LLM Imagen Processor

Generates images using configured Gemini imagen providers. Connect `Lumi LLM Imagen Provider` and `Lumi LLM Imagen Config` to this node.

Deprecated compatibility nodes remain registered for older workflows:
- `Lumi Gemini Imagen Config`
- `Lumi Google Imagen Provider`
- `Lumi OpenRouter Imagen Provider`

ComfyUI can migrate these deprecated nodes to the combined nodes through the registered node replacement mappings.

### Utility Nodes

#### Lumi Noise To Seed

Extracts an integer seed from a NOISE object for nodes that expect an INT seed.

#### Lumi Seed

Outputs a seed value with `control_after_generate` support (randomize, increment, decrement, fixed).

#### Lumi Save Image

Saves images as PNG with workflow metadata. If PNG exceeds 4MB, also saves a JPG version with configurable quality (default 100). Directory and filename are separate widgets, each supporting ComfyUI token replacements. Directory defaults to `%year%-%month%-%day%`.

## Configuring Wildcard Paths

Configure wildcard paths in `ComfyUI/extra_model_paths.yaml`:

```yaml
my_wildcards:
  wildcards: D:/dev/wildcards
```

Alternatively:

- Set the `LUMI_WILDCARDS_PATH` environment variable
- Place wildcards in `{ComfyUI}/wildcards`

## License

GPL-3.0
