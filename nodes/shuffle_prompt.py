"""
Lumi Shuffle Prompt node - shuffles tokens in a prompt.
"""
from __future__ import annotations

import random


class LumiShufflePrompt:
    """
    Shuffles tokens in a prompt string.
    
    Strips newlines and commas, splits by spaces, shuffles, and rejoins.
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "tooltip": "The prompt text to shuffle."}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for shuffling."}),
            },
        }

    CATEGORY = "Lumi/Prompt"
    DESCRIPTION = "Shuffles tokens in a prompt. Strips newlines and commas, splits by spaces, shuffles, and rejoins."

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("shuffled text",)
    FUNCTION = "shuffle"

    def shuffle(self, text: str, seed: int) -> tuple[str]:
        # Normalize to single line: replace newlines with spaces
        text = text.replace("\n", " ").replace("\r", " ")
        # Strip commas
        text = text.replace(",", "")
        # Tokenize by splitting on spaces (filter out empty tokens)
        tokens = [t for t in text.split(" ") if t]
        # Shuffle with seed
        rng = random.Random(seed)
        rng.shuffle(tokens)
        # Join back together
        result = " ".join(tokens)
        return (result,)

