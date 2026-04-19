"""
Lumi Seed node - outputs a random seed value.
"""

from __future__ import annotations

try:
    from comfy_api.latest import io
except ImportError:
    io = None


_ComfyNodeBase = io.ComfyNode if io is not None else object


class LumiSeed(_ComfyNodeBase):
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

    @classmethod
    def define_schema(cls):
        if io is None:
            raise RuntimeError("ComfyUI V3 API is not available")

        return io.Schema(
            node_id="LumiSeed",
            display_name="Lumi Seed",
            category="Lumi/Utils",
            description=cls.DESCRIPTION,
            inputs=[
                io.Int.Input(
                    "seed",
                    default=0,
                    min=0,
                    max=0xFFFFFFFF,
                    tooltip="The seed value to output.",
                    control_after_generate=True,
                )
            ],
            outputs=[io.Int.Output(display_name="seed")],
        )

    @classmethod
    def execute(cls, seed: int):
        if io is not None:
            return io.NodeOutput(seed)
        return (seed,)
