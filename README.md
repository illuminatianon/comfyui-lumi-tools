# Lumi Tools

A collection of utility nodes for ComfyUI.

## Installation

1. Clone or symlink this repository into your ComfyUI `custom_nodes` folder
2. Install dependencies:
   ```bash
   pip install .
   ```
3. Restart ComfyUI

## Nodes

All nodes appear under **Lumi/** in the node menu.

### Lumi Shuffle Prompt

Shuffles tokens in a prompt string. Useful for randomizing tag order.

- Strips newlines and commas
- Splits by spaces, shuffles, and rejoins
- Seeded for reproducibility

### Lumi Wildcard Processor

Processes wildcard prompts using [dynamicprompts](https://github.com/adieyal/dynamicprompts).

### Lumi Wildcard Encode

Processes wildcards with inline LoRA support and encodes to conditioning.

### Lumi Show Text

Displays text output for debugging.

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
