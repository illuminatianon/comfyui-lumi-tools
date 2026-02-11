"""
Lumi Show Text node - displays text output in the node.
"""

from __future__ import annotations

from typing import Any

PromptServer: Any = None
try:
    from server import (
        PromptServer as _PromptServer,  # type: ignore[reportMissingImports]
    )

    PromptServer = _PromptServer

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
            "hidden": {
                "unique_id": "UNIQUE_ID",
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    CATEGORY = "Lumi/Utils"
    DESCRIPTION = "Displays text output. Connect to any STRING output to view its contents."

    INPUT_IS_LIST = True
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    OUTPUT_IS_LIST = (True,)
    OUTPUT_NODE = True
    FUNCTION = "show"

    @staticmethod
    def _normalize_hidden(value):
        if isinstance(value, list) and value:
            return value[0]
        return value

    def show(self, text, unique_id=None, prompt=None, extra_pnginfo=None, **kwargs):
        display_text = "\n".join(text)
        node_id = self._normalize_hidden(unique_id)
        prompt_obj = self._normalize_hidden(prompt)
        extra_pnginfo_obj = self._normalize_hidden(extra_pnginfo)

        if node_id is not None and isinstance(prompt_obj, dict):
            node_key = str(node_id)
            prompt_node = prompt_obj.get(node_key)
            if isinstance(prompt_node, dict):
                prompt_inputs = prompt_node.get("inputs")
                if isinstance(prompt_inputs, dict):
                    prompt_inputs["displayed_text"] = display_text

        if node_id is not None and isinstance(extra_pnginfo_obj, dict):
            workflow = extra_pnginfo_obj.get("workflow")
            if isinstance(workflow, dict):
                workflow_nodes = workflow.get("nodes")
                if isinstance(workflow_nodes, list):
                    for node in workflow_nodes:
                        if not isinstance(node, dict):
                            continue
                        if str(node.get("id")) != str(node_id):
                            continue

                        widget_values = node.get("widgets_values")
                        if isinstance(widget_values, list):
                            if widget_values:
                                widget_values[-1] = display_text
                            else:
                                node["widgets_values"] = [display_text]
                        elif isinstance(widget_values, dict):
                            widget_values["displayed_text"] = display_text
                        break

        if HAS_SERVER and node_id is not None:
            PromptServer.instance.send_sync(
                "lumi-node-feedback",
                {
                    "node_id": node_id,
                    "widget_name": "displayed_text",
                    "value": display_text,
                },
            )

        return (text,)
