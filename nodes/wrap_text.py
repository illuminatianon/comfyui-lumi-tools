"""
Wrap Text node for prepending and appending text.
"""

from typing import Optional, Tuple

try:
    from comfy_api.latest import io
except ImportError:
    io = None


_ComfyNodeBase = io.ComfyNode if io is not None else object


class LumiWrapText(_ComfyNodeBase):
    """Wraps input text with prepend and append strings."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": (
                    "STRING",
                    {
                        "forceInput": True,
                        "tooltip": "Input text to wrap",
                    },
                ),
                "prepend": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Text to add before the input",
                    },
                ),
                "append": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Text to add after the input",
                    },
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "execute"
    CATEGORY = "Lumi/Text"

    DESCRIPTION = "Wraps input text by prepending and appending strings."

    @staticmethod
    def _wrap(text: Optional[str], prepend: Optional[str], append: Optional[str]) -> str:
        safe_prepend = prepend or ""
        safe_append = append or ""
        if text is None:
            raise ValueError(
                "Lumi Wrap Text received None for 'text'. Check upstream nodes for empty/failed output."
            )

        return safe_prepend + text + safe_append

    @classmethod
    def define_schema(cls):
        if io is None:
            raise RuntimeError("ComfyUI V3 API is not available")

        return io.Schema(
            node_id="LumiWrapText",
            display_name="Lumi Wrap Text",
            category="Lumi/Text",
            description=cls.DESCRIPTION,
            inputs=[
                io.String.Input("text", force_input=True, tooltip="Input text to wrap"),
                io.String.Input(
                    "prepend",
                    multiline=True,
                    default="",
                    tooltip="Text to add before the input",
                ),
                io.String.Input(
                    "append",
                    multiline=True,
                    default="",
                    tooltip="Text to add after the input",
                ),
            ],
            outputs=[io.String.Output(display_name="text")],
        )

    @classmethod
    def execute(cls, text: Optional[str], prepend: Optional[str], append: Optional[str]):
        result = cls._wrap(text, prepend, append)
        if io is not None:
            return io.NodeOutput(result)
        return (result,)

    def wrap_text(
        self, text: Optional[str], prepend: Optional[str], append: Optional[str]
    ) -> Tuple[str]:
        """Combine prepend + text + append."""
        return (self.__class__._wrap(text, prepend, append),)
