"""
Lumi Show Text node - displays text output in the node.
"""

from __future__ import annotations

try:
    from server import PromptServer

    HAS_SERVER = True
except ImportError:
    HAS_SERVER = False


class LumiShowText:
    """
    A simple node that displays any text passed to it.
    Useful for debugging and viewing text outputs from other nodes.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"forceInput": True}),
            },
            "optional": {
                "displayed_text": ("STRING", {"multiline": True, "default": ""}),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    CATEGORY = "Lumi/Utils"
    DESCRIPTION = "Displays text output. Connect to any STRING output to view its contents."

    INPUT_IS_LIST = True
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    OUTPUT_IS_LIST = (True,)
    OUTPUT_NODE = True
    FUNCTION = "show"

    def show(self, text, unique_id=None, **kwargs):
        display_text = "\n".join(text)

        if HAS_SERVER and unique_id is not None:
            PromptServer.instance.send_sync(
                "lumi-node-feedback",
                {
                    "node_id": unique_id,
                    "widget_name": "displayed_text",
                    "value": display_text,
                },
            )

        return (text,)
