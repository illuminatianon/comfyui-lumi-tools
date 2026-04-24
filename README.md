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

#### Lumi Gemini Imagen Config

Configuration node for Gemini image generation models. Sets aspect ratio (default: 16:9), image size (default: 2K), temperature, and top-p.

#### Lumi Google Imagen Provider

Direct Google AI Studio API provider for image generation. Uses `GOOGLE_API_KEY` environment variable. Much faster than OpenRouter (~4x).

Available models:
- `gemini-3-pro-image-preview` (default, supports up to 4K)
- `gemini-3.1-flash-image-preview` (supports up to 4K)
- `gemini-2.5-flash-image` (1K only)

#### Lumi OpenRouter Imagen Provider

OpenRouter API provider for Gemini image generation. Uses `OPENROUTER_API_KEY` environment variable.

Additional OpenRouter model:
- `google/gemini-2.0-flash-preview-image-generation` (OpenRouter only, 1K only)

#### Lumi OpenAI Imagen Config

Configuration node for OpenAI GPT Image models. Sets preset or custom resolution and quality. Custom resolutions use `WIDTHxHEIGHT` and are validated against OpenAI's `gpt-image-2` rules: max edge 3840px, both edges multiples of 16px, max 3:1 aspect ratio, and 655,360 to 8,294,400 total pixels.

#### Lumi OpenAI Imagen Provider

OpenAI API provider for GPT Image models. Uses `OPENAI_API_KEY` environment variable.

Available models:
- `gpt-image-2` (OpenAI default, supports custom valid sizes)
- `gpt-image-1` (OpenAI, supports `1024x1024`, `1536x1024`, and `1024x1536`)

#### Lumi LLM Imagen Processor

Generates images using configured Gemini or OpenAI imagen providers. Connect provider and config nodes. For OpenAI, the processor uses the Image Create endpoint when no `input_images` chain is connected and the Image Edit endpoint when an input image chain is provided.

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
