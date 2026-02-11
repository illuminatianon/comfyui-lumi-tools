"""
Lumi Noise To Seed node - extracts seed from NOISE objects.
"""

from __future__ import annotations

from typing import Any


class LumiNoiseToSeed:
    """Extracts the seed value from a NOISE object."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "noise": (
                    "NOISE",
                    {
                        "tooltip": "RandomNoise object to extract the seed from.",
                    },
                ),
            }
        }

    CATEGORY = "Lumi/Utils"
    DESCRIPTION = "Extracts the seed from a NOISE object for nodes expecting an INT seed."

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("seed",)
    FUNCTION = "extract_seed"

    def extract_seed(self, noise: Any) -> tuple[int]:
        seed = None

        if isinstance(noise, dict):
            seed = noise.get("seed")
        elif hasattr(noise, "seed"):
            seed = noise.seed

        if seed is None:
            raise ValueError("NOISE input does not include a seed value.")

        try:
            return (int(seed),)
        except (TypeError, ValueError) as exc:
            raise ValueError("NOISE seed value must be an integer.") from exc
