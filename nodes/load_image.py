"""Lumi Load Image node with ordered image-chain output."""

from __future__ import annotations

import hashlib
import os
from typing import Any, Iterable

import folder_paths
import node_helpers
import numpy as np
import torch
from PIL import Image, ImageOps, ImageSequence


def _list_single_image_tensors(images: torch.Tensor) -> list[torch.Tensor]:
    """Expand an IMAGE tensor into a list of single-image tensors."""
    if images.ndim == 3:
        return [images.unsqueeze(0)]
    if images.ndim != 4:
        raise ValueError(f"Expected image tensor with 3 or 4 dims, got shape {tuple(images.shape)}")
    return [images[i : i + 1] for i in range(images.shape[0])]


class LumiLoadImage:
    """Load an image and append it to an ordered image chain."""

    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]
        files = folder_paths.filter_files_content_types(files, ["image"])

        return {
            "required": {
                "image": (
                    sorted(files),
                    {
                        "image_upload": True,
                        "tooltip": "Image file to load from ComfyUI input directory",
                    },
                ),
            },
            "optional": {
                "image_chain": (
                    "LUMI_IMAGE_CHAIN",
                    {
                        "tooltip": "Optional chain from another Lumi Load Image node",
                    },
                ),
            },
        }

    CATEGORY = "Lumi/image"
    RETURN_TYPES = ("IMAGE", "MASK", "LUMI_IMAGE_CHAIN")
    RETURN_NAMES = ("image", "mask", "image_chain")
    FUNCTION = "load_image"

    DESCRIPTION = (
        "Loads an image like ComfyUI Load Image and emits an ordered image chain. "
        "Connect multiple Lumi Load Image nodes in sequence to preserve image order."
    )

    def load_image(
        self,
        image: str,
        image_chain: dict[str, list[torch.Tensor]] | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor, dict[str, list[torch.Tensor]]]:
        image_path = folder_paths.get_annotated_filepath(image)

        loaded = node_helpers.pillow(Image.open, image_path)
        output_images = []
        output_masks = []
        width, height = None, None

        for frame in ImageSequence.Iterator(loaded):
            frame = node_helpers.pillow(ImageOps.exif_transpose, frame)

            if frame.mode == "I":
                frame = frame.point(lambda i: i * (1 / 255))

            rgb = frame.convert("RGB")
            if len(output_images) == 0:
                width = rgb.size[0]
                height = rgb.size[1]

            if rgb.size[0] != width or rgb.size[1] != height:
                continue

            np_image = np.array(rgb).astype(np.float32) / 255.0
            output_images.append(torch.from_numpy(np_image)[None, ...])

            if "A" in frame.getbands():
                alpha = np.array(frame.getchannel("A")).astype(np.float32) / 255.0
                mask = 1.0 - torch.from_numpy(alpha)
            elif frame.mode == "P" and "transparency" in frame.info:
                alpha = np.array(frame.convert("RGBA").getchannel("A")).astype(np.float32) / 255.0
                mask = 1.0 - torch.from_numpy(alpha)
            else:
                mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")
            output_masks.append(mask.unsqueeze(0))

            if loaded.format == "MPO":
                break

        if len(output_images) > 1:
            image_tensor = torch.cat(output_images, dim=0)
            mask_tensor = torch.cat(output_masks, dim=0)
        else:
            image_tensor = output_images[0]
            mask_tensor = output_masks[0]

        merged_chain: list[torch.Tensor] = []
        if image_chain and isinstance(image_chain, dict):
            previous = image_chain.get("images", [])
            if isinstance(previous, Iterable):
                for item in previous:
                    if isinstance(item, torch.Tensor):
                        merged_chain.extend(_list_single_image_tensors(item))

        merged_chain.extend(_list_single_image_tensors(image_tensor))

        return (image_tensor, mask_tensor, {"images": merged_chain})

    @classmethod
    def IS_CHANGED(cls, image: str, image_chain: Any = None):
        image_path = folder_paths.get_annotated_filepath(image)
        digest = hashlib.sha256()
        with open(image_path, "rb") as file_handle:
            digest.update(file_handle.read())

        chain_len = 0
        if isinstance(image_chain, dict):
            chain_images = image_chain.get("images", [])
            if isinstance(chain_images, Iterable):
                chain_len = sum(1 for _ in chain_images)

        digest.update(str(chain_len).encode("utf-8"))
        return digest.hexdigest()

    @classmethod
    def VALIDATE_INPUTS(cls, image: str):
        if not folder_paths.exists_annotated_filepath(image):
            return f"Invalid image file: {image}"
        return True
