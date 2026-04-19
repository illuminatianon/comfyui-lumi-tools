"""
Lumi Noise To Seed node - extracts seed from NOISE objects.
"""

from __future__ import annotations

from typing import Any

try:
    from comfy_api.latest import io
except ImportError:
    io = None


_ComfyNodeBase = io.ComfyNode if io is not None else object


class LumiNoiseToSeed(_ComfyNodeBase):
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

    @staticmethod
    def _extract_seed_value(noise: Any) -> int:
        seed = None

        if isinstance(noise, dict):
            seed = noise.get("seed")
        elif hasattr(noise, "seed"):
            seed = noise.seed

        if seed is None:
            raise ValueError("NOISE input does not include a seed value.")

        try:
            return int(seed)
        except (TypeError, ValueError) as exc:
            raise ValueError("NOISE seed value must be an integer.") from exc

    @classmethod
    def define_schema(cls):
        if io is None:
            raise RuntimeError("ComfyUI V3 API is not available")

        noise_type = io.Custom("NOISE")
        return io.Schema(
            node_id="LumiNoiseToSeed",
            display_name="Lumi Noise To Seed",
            category="Lumi/Utils",
            description=cls.DESCRIPTION,
            inputs=[
                noise_type.Input(
                    "noise",
                    tooltip="RandomNoise object to extract the seed from.",
                )
            ],
            outputs=[io.Int.Output(display_name="seed")],
        )

    @classmethod
    def execute(cls, noise: Any):
        seed_value = cls._extract_seed_value(noise)

        if io is not None:
            return io.NodeOutput(seed_value)
        return (seed_value,)

    def extract_seed(self, noise: Any) -> tuple[int]:
        return (self.__class__._extract_seed_value(noise),)
