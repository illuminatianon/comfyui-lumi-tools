"""
Lumi Text Input node - supplies a multiline string input.
"""

from __future__ import annotations

try:
    from comfy_api.latest import io
except ImportError:
    io = None


_ComfyNodeBase = io.ComfyNode if io is not None else object


class LumiTextInput(_ComfyNodeBase):
    """Outputs the provided text input."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Text to output.",
                    },
                ),
            }
        }

    CATEGORY = "Lumi/Text"
    DESCRIPTION = "Provides an arbitrary multiline text input."

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "get_text"

    @classmethod
    def define_schema(cls):
        if io is None:
            raise RuntimeError("ComfyUI V3 API is not available")

        return io.Schema(
            node_id="LumiTextInput",
            display_name="Lumi Text Input",
            category="Lumi/Text",
            description=cls.DESCRIPTION,
            inputs=[
                io.String.Input(
                    "text",
                    multiline=True,
                    default="",
                    tooltip="Text to output.",
                )
            ],
            outputs=[io.String.Output(display_name="text")],
        )

    @classmethod
    def execute(cls, text: str):
        if io is not None:
            return io.NodeOutput(text)
        return (text,)

    def get_text(self, text: str) -> tuple[str]:
        return (text,)
