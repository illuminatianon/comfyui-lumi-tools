"""
Lumi Show Text node - displays text output in the node.
"""

from __future__ import annotations

from typing import Any

try:
    from comfy_api.latest import io
except ImportError:
    io = None


_ComfyNodeBase = io.ComfyNode if io is not None else object

PromptServer: Any = None
try:
    from server import (
        PromptServer as _PromptServer,  # type: ignore[reportMissingImports]
    )

    PromptServer = _PromptServer

    HAS_SERVER = True
except ImportError:
    HAS_SERVER = False


class LumiShowText(_ComfyNodeBase):
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
    FUNCTION = "execute"

    @staticmethod
    def _normalize_hidden(value):
        if isinstance(value, list) and value:
            return value[0]
        return value

    @classmethod
    def define_schema(cls):
        if io is None:
            raise RuntimeError("ComfyUI V3 API is not available")

        return io.Schema(
            node_id="LumiShowText",
            display_name="Lumi Show Text",
            category="Lumi/Utils",
            description=cls.DESCRIPTION,
            is_output_node=True,
            is_input_list=True,
            hidden=[io.Hidden.unique_id, io.Hidden.prompt, io.Hidden.extra_pnginfo],
            inputs=[
                io.String.Input("text", force_input=True),
                io.String.Input("displayed_text", multiline=True, default="", optional=True),
            ],
            outputs=[io.String.Output(display_name="text", is_output_list=True)],
        )

    @classmethod
    def execute(cls, text, displayed_text=""):
        del displayed_text

        unique_id = None
        prompt = None
        extra_pnginfo = None
        if io is not None and getattr(cls, "hidden", None) is not None:
            unique_id = getattr(cls.hidden, "unique_id", None)
            prompt = getattr(cls.hidden, "prompt", None)
            extra_pnginfo = getattr(cls.hidden, "extra_pnginfo", None)

        text_value = text if isinstance(text, list) else [text]
        output = cls._show_impl(
            text_value, unique_id=unique_id, prompt=prompt, extra_pnginfo=extra_pnginfo
        )
        if io is not None:
            return io.NodeOutput(output)
        return (output,)

    @classmethod
    def _show_impl(cls, text, unique_id=None, prompt=None, extra_pnginfo=None):
        display_text = "\n".join(text)
        node_id = cls._normalize_hidden(unique_id)
        prompt_obj = cls._normalize_hidden(prompt)
        extra_pnginfo_obj = cls._normalize_hidden(extra_pnginfo)

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

        return text

    def show(self, text, unique_id=None, prompt=None, extra_pnginfo=None, **kwargs):
        del kwargs
        return (
            self.__class__._show_impl(
                text,
                unique_id=unique_id,
                prompt=prompt,
                extra_pnginfo=extra_pnginfo,
            ),
        )
