"""
Lumi Seed node - outputs a random seed value.
"""

from __future__ import annotations


class LumiSeed:
    """
    Outputs a random seed value.

    The seed widget automatically includes ComfyUI's 'control_after_generate'
    functionality (randomize, increment, decrement, fixed).
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xFFFFFFFF,
                        "tooltip": "The seed value to output.",
                        "control_after_generate": True,
                    },
                ),
            },
        }

    CATEGORY = "Lumi/Utils"
    DESCRIPTION = "Outputs a seed value. Includes control_after_generate for randomizing, incrementing, or fixing the seed."

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("seed",)
    FUNCTION = "execute"

    def execute(self, seed: int) -> tuple[int]:
        return (seed,)

