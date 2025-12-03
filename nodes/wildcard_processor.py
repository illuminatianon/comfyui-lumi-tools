"""
Lumi Wildcard Processor node.

Based on ComfyUI-Impact-Pack's Wildcard Processor node.
"""
from __future__ import annotations

from .wildcards import get_wildcard_list, process_wildcards

try:
    from server import PromptServer
    HAS_SERVER = True
except ImportError:
    HAS_SERVER = False


class LumiWildcardProcessor:

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
                        "wildcard_text": ("STRING", {"multiline": True, "dynamicPrompts": False, "tooltip": "Enter a prompt using wildcard syntax."}),
                        "populated_text": ("STRING", {"multiline": True, "dynamicPrompts": False, "tooltip": "The actual value passed during execution. Wildcard syntax can also be used here."}),
                        "mode": (["populate", "fixed", "reproduce"], {"default": "populate", "tooltip":
                            "populate: Overwrites 'populated_text' with the processed prompt from 'wildcard_text'. Cannot edit 'populated_text' in this mode.\n"
                            "fixed: Ignores wildcard_text and keeps 'populated_text' as is. You can edit 'populated_text' in this mode.\n"
                            "reproduce: Operates as 'fixed' mode once for reproduction, then switches to 'populate' mode."
                            }),
                        "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for wildcard processing."}),
                        "Select to add Wildcard": (get_wildcard_list(),),
                    },
                "hidden": {"unique_id": "UNIQUE_ID"},
                }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Force re-evaluation to refresh wildcard list
        return float("NaN")

    CATEGORY = "Lumi/Prompt"

    DESCRIPTION = "Processes text prompts written in wildcard syntax and outputs the processed text prompt."

    RETURN_TYPES = ("STRING", )
    RETURN_NAMES = ("processed text",)
    FUNCTION = "doit"

    def doit(self, **kwargs):
        mode = kwargs.get('mode', 'populate')
        seed = kwargs['seed']
        unique_id = kwargs.get('unique_id')

        if mode == 'populate':
            # Process wildcard_text and return result
            result = process_wildcards(text=kwargs['wildcard_text'], seed=seed)
        else:
            # fixed/reproduce: use populated_text as-is (but still process any wildcards in it)
            result = process_wildcards(text=kwargs['populated_text'], seed=seed)

        # Send feedback to update the populated_text widget in the UI
        if HAS_SERVER and unique_id is not None:
            PromptServer.instance.send_sync(
                "lumi-node-feedback",
                {"node_id": unique_id, "widget_name": "populated_text", "value": result}
            )

        return (result, )

