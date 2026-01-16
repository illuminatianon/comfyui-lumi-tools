"""
Lumi Text Input node - supplies a multiline string input.
"""

from __future__ import annotations


class LumiTextInput:
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

    def get_text(self, text: str) -> tuple[str]:
        return (text,)
