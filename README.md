# Lumi Wildcard Processor

A ComfyUI custom node for processing wildcard prompts using the [dynamicprompts](https://github.com/adieyal/dynamicprompts) library.

## Installation

1. Clone or symlink this repository into your ComfyUI `custom_nodes` folder
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Restart ComfyUI

## Usage

The node appears under **Lumi/Prompt** as "Lumi Wildcard Processor".

For wildcard syntax documentation, see the [dynamicprompts documentation](https://github.com/adieyal/dynamicprompts#syntax).

### Modes

- **populate**: Processes `wildcard_text` and writes the result to `populated_text`
- **fixed**: Ignores `wildcard_text`, uses `populated_text` as-is (allows manual editing)
- **reproduce**: Runs as `fixed` once for reproduction, then switches to `populate`

## Configuring Wildcard Paths

Wildcards are loaded from `.txt`, `.yaml`, or `.json` files. The node searches for wildcards in the following locations (in order):

### 1. Environment Variable

Set `LUMI_WILDCARDS_PATH` to point to your wildcards folder:

```bash
# Windows
set LUMI_WILDCARDS_PATH=D:\my\wildcards

# Linux/Mac
export LUMI_WILDCARDS_PATH=/home/user/my/wildcards
```

### 2. ComfyUI extra_model_paths.yaml (Recommended)

Add a `wildcards` entry to your `ComfyUI/extra_model_paths.yaml`:

```yaml
my_config:
  wildcards: D:/dev/wildcards
```

You can specify multiple sources:

```yaml
personal_wildcards:
  wildcards: D:/my/personal/wildcards

shared_wildcards:
  wildcards: //server/shared/wildcards
```

All paths are merged, so wildcards from all locations are available.

### 3. Default Location

If no custom paths are configured, wildcards are loaded from `{ComfyUI}/wildcards`.

### 4. Local ./wildcards Folder

You can also place wildcards in the `wildcards` folder inside this node's directory. This is checked last and not recommended for general use (keep your data separate from your code), but it works if you really want it.

## License

GPL-3.0 (derived from [ComfyUI-Impact-Pack](https://github.com/ltdrdata/ComfyUI-Impact-Pack))
