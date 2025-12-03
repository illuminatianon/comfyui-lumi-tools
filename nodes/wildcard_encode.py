"""
Lumi Wildcard Encode node - processes wildcards, loads LoRAs, and encodes to conditioning.

Based on ComfyUI-Impact-Pack's Wildcard Encode node.
"""
from __future__ import annotations

import logging
import re

import folder_paths
import nodes

from .wildcards import get_wildcard_list, process_wildcards

try:
    from server import PromptServer
    HAS_SERVER = True
except ImportError:
    HAS_SERVER = False


def is_numeric_string(input_str: str) -> bool:
    """Check if string represents a numeric value."""
    return re.match(r'^-?(\d*\.?\d+|\d+\.?\d*)$', input_str) is not None


def safe_float(x: str) -> float:
    """Safely convert string to float, defaulting to 1.0."""
    if is_numeric_string(x):
        return float(x)
    return 1.0


def extract_lora_values(string: str) -> list[tuple]:
    """
    Extract LoRA tags from text.
    
    Supports syntax: <lora:name:model_weight:clip_weight:LBW=preset:LOADER=type>
    
    Returns list of tuples: (lora_name, model_weight, clip_weight, lbw, lbw_a, lbw_b, loader)
    """
    pattern = r'<lora:([^>]+)>'
    matches = re.findall(pattern, string)

    def touch_lbw(text):
        return re.sub(r'LBW=[A-Za-z][A-Za-z0-9_-]*:', r'LBW=', text)

    items = [touch_lbw(match.strip(':')) for match in matches]

    added = set()
    result = []
    for item in items:
        item = item.split(':')

        lora = None
        a = None
        b = None
        lbw = None
        lbw_a = None
        lbw_b = None
        loader = None

        if len(item) > 0:
            lora = item[0]

            for sub_item in item[1:]:
                if is_numeric_string(sub_item):
                    if a is None:
                        a = float(sub_item)
                    elif b is None:
                        b = float(sub_item)
                elif sub_item.startswith("LBW="):
                    for lbw_item in sub_item[4:].split(';'):
                        if lbw_item.startswith("A="):
                            lbw_a = safe_float(lbw_item[2:].strip())
                        elif lbw_item.startswith("B="):
                            lbw_b = safe_float(lbw_item[2:].strip())
                        elif lbw_item.strip() != '':
                            lbw = lbw_item
                elif sub_item.startswith("LOADER="):
                    loader = sub_item[7:]

        if a is None:
            a = 1.0
        if b is None:
            b = a

        if lora is not None and lora not in added:
            result.append((lora, a, b, lbw, lbw_a, lbw_b, loader))
            added.add(lora)

    return result


def remove_lora_tags(string: str) -> str:
    """Remove all <lora:...> tags from text."""
    pattern = r'<lora:[^>]+>'
    return re.sub(pattern, '', string)


def resolve_lora_name(lora_name_cache: list[str], name: str) -> str | None:
    """Resolve a partial LoRA name to a full path."""
    import os
    if os.path.exists(name):
        return name
    
    if len(lora_name_cache) == 0:
        lora_name_cache.extend(folder_paths.get_filename_list("loras"))

    for x in lora_name_cache:
        if x.endswith(name):
            return x

    return None


def process_with_loras(wildcard_opt: str, model, clip, seed: int = None) -> tuple:
    """
    Process wildcard text including LoRA tags and encode to conditioning.
    
    Args:
        wildcard_opt: Text with wildcard syntax and optional <lora:...> tags
        model: The MODEL input
        clip: The CLIP input  
        seed: Random seed for wildcard processing
        
    Returns:
        tuple: (model, clip, conditioning, processed_text)
    """
    lora_name_cache = []

    # Pass 1: Process wildcards
    pass1 = process_wildcards(wildcard_opt, seed or 0)
    
    # Extract and remove LoRA tags
    loras = extract_lora_values(pass1)
    pass2 = remove_lora_tags(pass1)

    # Load LoRAs
    for lora_name, model_weight, clip_weight, lbw, lbw_a, lbw_b, loader in loras:
        lora_name_ext = lora_name.split('.')
        if ('.' + lora_name_ext[-1]) not in folder_paths.supported_pt_extensions:
            lora_name = lora_name + ".safetensors"

        orig_lora_name = lora_name
        lora_name = resolve_lora_name(lora_name_cache, lora_name)

        if lora_name is not None:
            path = folder_paths.get_full_path("loras", lora_name)
        else:
            path = None

        if path is not None:
            logging.info(f"[Lumi Pack] LOAD LORA: {lora_name}: {model_weight}, {clip_weight}, LBW={lbw}")

            if loader is not None:
                if loader == 'nunchaku':
                    if 'NunchakuFluxLoraLoader' not in nodes.NODE_CLASS_MAPPINGS:
                        logging.warning("[Lumi Pack] LOADER=nunchaku requires ComfyUI-nunchaku. Ignoring.")
                    else:
                        cls = nodes.NODE_CLASS_MAPPINGS['NunchakuFluxLoraLoader']
                        model = cls().load_lora(model, lora_name, model_weight)[0]
                else:
                    logging.warning(f"[Lumi Pack] Unknown LOADER: '{loader}'")
            else:
                def default_lora():
                    return nodes.LoraLoader().load_lora(model, clip, lora_name, model_weight, clip_weight)

                if lbw is not None:
                    if 'LoraLoaderBlockWeight //Inspire' not in nodes.NODE_CLASS_MAPPINGS:
                        logging.warning("[Lumi Pack] LBW syntax requires Inspire Pack. Ignoring LBW.")
                        model, clip = default_lora()
                    else:
                        cls = nodes.NODE_CLASS_MAPPINGS['LoraLoaderBlockWeight //Inspire']
                        model, clip, _ = cls().doit(model, clip, lora_name, model_weight, clip_weight, False, 0, lbw_a, lbw_b, "", lbw)
                else:
                    model, clip = default_lora()
        else:
            logging.warning(f"[Lumi Pack] LORA NOT FOUND: {orig_lora_name}")

    # Pass 3: Split by BREAK and encode each segment
    pass3 = [x.strip() for x in pass2.split("BREAK")]
    pass3 = [x for x in pass3 if x != '']

    if len(pass3) == 0:
        pass3 = ['']

    logging.info(f"[Lumi Pack] CLIP segments: {[f'[{x}]' for x in pass3]}")

    # Encode and concatenate conditioning
    result = None
    for prompt in pass3:
        cur = nodes.CLIPTextEncode().encode(clip, prompt)[0]
        if result is not None:
            result = nodes.ConditioningConcat().concat(result, cur)[0]
        else:
            result = cur

    return model, clip, result, pass1


class LumiWildcardEncode:
    """
    Processes wildcard text, loads LoRAs inline, and encodes to conditioning.

    LoRA Syntax: <lora:name:model_weight:clip_weight>
    Supports BREAK keyword for conditioning concatenation.
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "wildcard_text": ("STRING", {"multiline": True, "dynamicPrompts": False,
                    "tooltip": "Enter a prompt using wildcard syntax. Supports <lora:name:weight> tags."}),
                "populated_text": ("STRING", {"multiline": True, "dynamicPrompts": False,
                    "tooltip": "The processed prompt shown after execution. Editable in 'fixed' mode."}),
                "mode": (["populate", "fixed", "reproduce"], {"default": "populate", "tooltip":
                    "populate: Processes 'wildcard_text' and updates 'populated_text'. Cannot edit 'populated_text'.\n"
                    "fixed: Ignores wildcard_text, uses 'populated_text' as-is. You can edit it.\n"
                    "reproduce: Uses 'fixed' mode once, then switches to 'populate'."}),
                "Select to add LoRA": (["Select the LoRA to add to the text"] + folder_paths.get_filename_list("loras"),),
                "Select to add Wildcard": (get_wildcard_list(),),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff,
                    "tooltip": "Random seed for wildcard processing."}),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    CATEGORY = "Lumi/Prompt"

    DESCRIPTION = (
        "Processes wildcard text with LoRA support and outputs conditioning.\n\n"
        "LoRA Syntax: <lora:name:model_weight:clip_weight>\n"
        "Use BREAK to concatenate multiple conditioning segments.\n\n"
        "If Inspire Pack is installed, LBW (LoRA Block Weight) syntax is also supported."
    )

    RETURN_TYPES = ("MODEL", "CLIP", "CONDITIONING", "STRING")
    RETURN_NAMES = ("model", "clip", "conditioning", "populated_text")
    FUNCTION = "doit"

    def doit(self, model, clip, wildcard_text, populated_text, mode, seed, unique_id=None, **kwargs):
        if mode == 'populate':
            text_to_process = wildcard_text
        else:
            text_to_process = populated_text

        model, clip, conditioning, processed_text = process_with_loras(
            wildcard_opt=text_to_process,
            model=model,
            clip=clip,
            seed=seed
        )

        # Send feedback to update the populated_text widget
        if HAS_SERVER and unique_id is not None:
            PromptServer.instance.send_sync(
                "lumi-node-feedback",
                {"node_id": unique_id, "widget_name": "populated_text", "value": processed_text}
            )

        return (model, clip, conditioning, processed_text)

