"""Lumi node that removes the alpha channel from RGBA image tensors."""

from __future__ import annotations

import torch

try:
    from comfy_api.latest import io
except ImportError:
    io = None


_ComfyNodeBase = io.ComfyNode if io is not None else object


class LumiRGBAtoRGB(_ComfyNodeBase):
    """Convert an RGBA IMAGE tensor to RGB by dropping its alpha channel."""

    CATEGORY = "Lumi/image"
    DESCRIPTION = "Converts an RGBA image to RGB by dropping the alpha channel."
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "convert"

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, dict[str, tuple[str]]]:
        return {"required": {"image": ("IMAGE",)}}

    @staticmethod
    def _drop_alpha(image: torch.Tensor) -> torch.Tensor:
        if image.ndim not in (3, 4) or image.shape[-1] != 4:
            raise ValueError(
                "Expected an RGBA IMAGE tensor with shape [height, width, 4] "
                "or [batch, height, width, 4], "
                f"got {tuple(image.shape)}"
            )
        return image[..., :3]

    @classmethod
    def define_schema(cls):
        if io is None:
            raise RuntimeError("ComfyUI V3 API is not available")

        return io.Schema(
            node_id="LumiRGBAtoRGB",
            display_name="Lumi RGBA to RGB",
            category=cls.CATEGORY,
            description=cls.DESCRIPTION,
            inputs=[io.Image.Input("image")],
            outputs=[io.Image.Output(display_name="image")],
        )

    @classmethod
    def execute(cls, image: torch.Tensor):
        rgb_image = cls._drop_alpha(image)
        if io is not None:
            return io.NodeOutput(rgb_image)
        return (rgb_image,)

    def convert(self, image: torch.Tensor) -> tuple[torch.Tensor]:
        return (self._drop_alpha(image),)
