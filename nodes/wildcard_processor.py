"""
Lumi Wildcard Processor node.

Based on ComfyUI-Impact-Pack's Wildcard Processor node.
"""

from __future__ import annotations

from .wildcards import get_wildcard_list, process_wildcards

try:
    from comfy_api.latest import io
except ImportError:
    io = None


_ComfyNodeBase = io.ComfyNode if io is not None else object

try:
    from server import PromptServer

    HAS_SERVER = True
except ImportError:
    HAS_SERVER = False


class LumiWildcardProcessor(_ComfyNodeBase):

    @classmethod
    def INPUT_TYPES(s):
        wildcard_options = tuple(get_wildcard_list())
        return {
            "required": {
                "wildcard_text": (
                    "STRING",
                    {
                        "multiline": True,
                        "dynamicPrompts": False,
                        "tooltip": "Enter a prompt using wildcard syntax.",
                    },
                ),
                "populated_text": (
                    "STRING",
                    {
                        "multiline": True,
                        "dynamicPrompts": False,
                        "tooltip": "The actual value passed during execution. Wildcard syntax can also be used here.",
                    },
                ),
                "mode": (
                    ("populate", "fixed", "reproduce"),
                    {
                        "default": "populate",
                        "tooltip": "populate: Overwrites 'populated_text' with the processed prompt from 'wildcard_text'. Cannot edit 'populated_text' in this mode.\n"
                        "fixed: Ignores wildcard_text and keeps 'populated_text' as is. You can edit 'populated_text' in this mode.\n"
                        "reproduce: Operates as 'fixed' mode once for reproduction, then switches to 'populate' mode.",
                    },
                ),
                "seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "tooltip": "Random seed for wildcard processing.",
                    },
                ),
            },
            "optional": {
                "Select to add Wildcard": (wildcard_options,),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Force re-evaluation to refresh wildcard list
        return float("NaN")

    CATEGORY = "Lumi/Prompt"

    DESCRIPTION = (
        "Processes text prompts written in wildcard syntax and outputs the processed text prompt."
    )

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("processed text",)
    FUNCTION = "execute"

    @classmethod
    def define_schema(cls):
        if io is None:
            raise RuntimeError("ComfyUI V3 API is not available")

        wildcard_options = tuple(get_wildcard_list())
        return io.Schema(
            node_id="LumiWildcardProcessor",
            display_name="Lumi Wildcard Processor",
            category="Lumi/Prompt",
            description=cls.DESCRIPTION,
            hidden=[io.Hidden.unique_id],
            inputs=[
                io.String.Input(
                    "wildcard_text",
                    multiline=True,
                    tooltip="Enter a prompt using wildcard syntax.",
                ),
                io.String.Input(
                    "populated_text",
                    multiline=True,
                    tooltip="The actual value passed during execution. Wildcard syntax can also be used here.",
                ),
                io.Combo.Input(
                    "mode",
                    options=("populate", "fixed", "reproduce"),
                    default="populate",
                    tooltip="populate: Overwrites 'populated_text' with processed 'wildcard_text'. fixed: Uses populated_text. reproduce: one-shot fixed then populate.",
                ),
                io.Int.Input(
                    "seed",
                    default=0,
                    min=0,
                    max=0xFFFFFFFFFFFFFFFF,
                    tooltip="Random seed for wildcard processing.",
                ),
                io.Combo.Input(
                    "select_wildcard",
                    display_name="Select to add Wildcard",
                    options=wildcard_options,
                    default=wildcard_options[0] if wildcard_options else "",
                    optional=True,
                    advanced=True,
                ),
            ],
            outputs=[io.String.Output(display_name="processed text")],
        )

    @classmethod
    def execute(
        cls,
        wildcard_text: str,
        populated_text: str,
        mode: str,
        seed: int,
        select_wildcard: str = "",
    ):
        del select_wildcard

        if mode == "populate":
            result = process_wildcards(text=wildcard_text, seed=seed)
        else:
            result = process_wildcards(text=populated_text, seed=seed)

        unique_id = None
        if io is not None and getattr(cls, "hidden", None) is not None:
            unique_id = getattr(cls.hidden, "unique_id", None)

        if HAS_SERVER and unique_id is not None:
            PromptServer.instance.send_sync(
                "lumi-node-feedback",
                {
                    "node_id": unique_id,
                    "widget_name": "populated_text",
                    "value": result,
                },
            )

        if io is not None:
            return io.NodeOutput(result)
        return (result,)

    def doit(self, **kwargs):
        mode = kwargs.get("mode", "populate")
        seed = kwargs["seed"]
        if mode == "populate":
            result = process_wildcards(text=kwargs["wildcard_text"], seed=seed)
        else:
            result = process_wildcards(text=kwargs["populated_text"], seed=seed)

        unique_id = kwargs.get("unique_id")
        if HAS_SERVER and unique_id is not None:
            PromptServer.instance.send_sync(
                "lumi-node-feedback",
                {
                    "node_id": unique_id,
                    "widget_name": "populated_text",
                    "value": result,
                },
            )

        return (result,)

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        return float("NaN")
