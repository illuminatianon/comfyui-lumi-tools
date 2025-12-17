"""
Wrap Text node for prepending and appending text.
"""

from typing import Tuple


class LumiWrapText:
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
    FUNCTION = "wrap_text"
    CATEGORY = "Lumi/Text"

    DESCRIPTION = "Wraps input text by prepending and appending strings."

    def wrap_text(self, text: str, prepend: str, append: str) -> Tuple[str]:
        """Combine prepend + text + append."""
        result = prepend + text + append
        return (result,)
