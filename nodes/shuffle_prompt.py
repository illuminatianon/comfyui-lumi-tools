"""
Lumi Shuffle Prompt node - shuffles tokens in a prompt.
"""

from __future__ import annotations

import random

try:
    from comfy_api.latest import io
except ImportError:
    io = None


_ComfyNodeBase = io.ComfyNode if io is not None else object


class LumiShufflePrompt(_ComfyNodeBase):
    """
    Shuffles tokens in a prompt string.

    Strips newlines and commas, splits by spaces, shuffles, and rejoins.
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": (
                    "STRING",
                    {"multiline": True, "tooltip": "The prompt text to shuffle."},
                ),
                "seed": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "tooltip": "Random seed for shuffling.",
                    },
                ),
            },
        }

    CATEGORY = "Lumi/Prompt"
    DESCRIPTION = "Shuffles tokens in a prompt. Strips newlines and commas, splits by spaces, shuffles, and rejoins."

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("shuffled text",)
    FUNCTION = "shuffle"

    @staticmethod
    def _shuffle_text(text: str, seed: int) -> str:
        normalized = text.replace("\n", " ").replace("\r", " ").replace(",", "")
        tokens = [t for t in normalized.split(" ") if t]
        rng = random.Random(seed)
        rng.shuffle(tokens)
        return " ".join(tokens)

    @classmethod
    def define_schema(cls):
        if io is None:
            raise RuntimeError("ComfyUI V3 API is not available")

        return io.Schema(
            node_id="LumiShufflePrompt",
            display_name="Lumi Shuffle Prompt",
            category="Lumi/Prompt",
            description=cls.DESCRIPTION,
            inputs=[
                io.String.Input(
                    "text",
                    multiline=True,
                    tooltip="The prompt text to shuffle.",
                ),
                io.Int.Input(
                    "seed",
                    default=0,
                    min=0,
                    max=0xFFFFFFFFFFFFFFFF,
                    tooltip="Random seed for shuffling.",
                ),
            ],
            outputs=[io.String.Output(display_name="shuffled text")],
        )

    @classmethod
    def execute(cls, text: str, seed: int):
        result = cls._shuffle_text(text, seed)
        if io is not None:
            return io.NodeOutput(result)
        return (result,)

    def shuffle(self, text: str, seed: int) -> tuple[str]:
        return (self.__class__._shuffle_text(text, seed),)
