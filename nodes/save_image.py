"""
Lumi Save Image node - saves PNG with optional JPG fallback for large files.
"""

import json
import os
from copy import deepcopy

import folder_paths
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

try:
    from comfy_api.latest import io
except ImportError:
    io = None


_ComfyNodeBase = io.ComfyNode if io is not None else object

# 4MB threshold for JPG fallback
SIZE_THRESHOLD_BYTES = 4 * 1024 * 1024


class LumiSaveImage(_ComfyNodeBase):
    """
    Save images to disk. If PNG exceeds 4MB, also saves a JPG version.
    Separate widgets handle directory and filename.
    """

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "directory": (
                    "STRING",
                    {
                        "default": "%year%-%month%-%day%",
                        "tooltip": "Output subfolder (e.g., 'my_project/renders')",
                    },
                ),
                "filename": (
                    "STRING",
                    {
                        "default": "ComfyUI",
                        "tooltip": "Base filename prefix for the saved images",
                    },
                ),
            },
            "optional": {
                "jpg_quality": (
                    "INT",
                    {
                        "default": 100,
                        "min": 1,
                        "max": 100,
                        "step": 1,
                        "tooltip": "JPEG quality (1-100) when PNG exceeds 4MB",
                    },
                ),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ()
    FUNCTION = "execute"
    OUTPUT_NODE = True
    CATEGORY = "Lumi/image"
    DESCRIPTION = "Save images as PNG. If PNG > 4MB, also saves a JPG version."

    @classmethod
    def define_schema(cls):
        if io is None:
            raise RuntimeError("ComfyUI V3 API is not available")

        return io.Schema(
            node_id="LumiSaveImage",
            display_name="Lumi Save Image",
            category="Lumi/image",
            description=cls.DESCRIPTION,
            is_output_node=True,
            hidden=[io.Hidden.prompt, io.Hidden.extra_pnginfo],
            inputs=[
                io.Image.Input("images"),
                io.String.Input(
                    "directory",
                    default="%year%-%month%-%day%",
                    tooltip="Output subfolder (e.g., 'my_project/renders')",
                ),
                io.String.Input(
                    "filename",
                    default="ComfyUI",
                    tooltip="Base filename prefix for the saved images",
                ),
                io.Int.Input(
                    "jpg_quality",
                    default=100,
                    min=1,
                    max=100,
                    step=1,
                    tooltip="JPEG quality (1-100) when PNG exceeds 4MB",
                    optional=True,
                ),
            ],
            outputs=[],
        )

    @classmethod
    def _save_images_impl(
        cls,
        images,
        directory,
        filename,
        jpg_quality,
        prompt,
        extra_pnginfo,
    ):
        output_dir = folder_paths.get_output_directory()
        output_type = "output"
        compress_level = 4

        if directory:
            full_prefix = os.path.join(directory, filename)
        else:
            full_prefix = filename

        (
            full_output_folder,
            resolved_filename,
            counter,
            subfolder,
            _,
        ) = folder_paths.get_save_image_path(
            full_prefix, output_dir, images[0].shape[1], images[0].shape[0]
        )

        results = []

        prompt_snapshot = deepcopy(prompt) if prompt is not None else None
        extra_pnginfo_snapshot = deepcopy(extra_pnginfo) if extra_pnginfo is not None else None

        for batch_number, image in enumerate(images):
            i = 255.0 * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

            metadata = None
            try:
                from comfy.cli_args import args

                if not args.disable_metadata:
                    metadata = PngInfo()
                    if prompt_snapshot is not None:
                        metadata.add_text("prompt", json.dumps(prompt_snapshot))
                    if extra_pnginfo_snapshot is not None:
                        for x in extra_pnginfo_snapshot:
                            metadata.add_text(x, json.dumps(extra_pnginfo_snapshot[x]))
            except Exception:
                pass

            filename_with_batch = resolved_filename.replace("%batch_num%", str(batch_number))
            png_file = f"{filename_with_batch}_{counter:05}_.png"
            png_path = os.path.join(full_output_folder, png_file)

            img.save(png_path, pnginfo=metadata, compress_level=compress_level)

            png_size = os.path.getsize(png_path)
            if png_size > SIZE_THRESHOLD_BYTES:
                jpg_file = f"{filename_with_batch}_{counter:05}_.jpg"
                jpg_path = os.path.join(full_output_folder, jpg_file)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(jpg_path, quality=jpg_quality, optimize=True)

            results.append({"filename": png_file, "subfolder": subfolder, "type": output_type})
            counter += 1

        return {"ui": {"images": results}}

    @classmethod
    def execute(cls, images, directory="", filename="ComfyUI", jpg_quality=100):
        prompt = None
        extra_pnginfo = None
        if io is not None and getattr(cls, "hidden", None) is not None:
            prompt = getattr(cls.hidden, "prompt", None)
            extra_pnginfo = getattr(cls.hidden, "extra_pnginfo", None)

        result = cls._save_images_impl(
            images,
            directory=directory,
            filename=filename,
            jpg_quality=jpg_quality,
            prompt=prompt,
            extra_pnginfo=extra_pnginfo,
        )
        if io is not None:
            return io.NodeOutput(ui=result["ui"])
        return result

    def save_images(
        self,
        images,
        directory="",
        filename="ComfyUI",
        jpg_quality=100,
        prompt=None,
        extra_pnginfo=None,
    ):
        return self.__class__._save_images_impl(
            images,
            directory=directory,
            filename=filename,
            jpg_quality=jpg_quality,
            prompt=prompt,
            extra_pnginfo=extra_pnginfo,
        )
