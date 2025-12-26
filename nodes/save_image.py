"""
Lumi Save Image node - saves PNG with optional JPG fallback for large files.
"""

import json
import os

import folder_paths
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo

# 4MB threshold for JPG fallback
SIZE_THRESHOLD_BYTES = 4 * 1024 * 1024


class LumiSaveImage:
    """
    Save images to disk. If PNG exceeds 4MB, also saves a JPG version.
    Path is a separate widget for clarity.
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
                "path": (
                    "STRING",
                    {
                        "default": "%year%-%month%-%day%",
                        "tooltip": "Subfolder path (e.g., 'my_project/renders')",
                    },
                ),
                "filename_prefix": (
                    "STRING",
                    {"default": "ComfyUI", "tooltip": "Prefix for the filename"},
                ),
            },
            "optional": {
                "jpg_quality": (
                    "INT",
                    {
                        "default": 90,
                        "min": 1,
                        "max": 100,
                        "step": 1,
                        "tooltip": "JPEG quality (1-100) for fallback saves",
                    },
                ),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "Lumi/image"
    DESCRIPTION = "Save images as PNG. If PNG > 4MB, also saves a JPG version."

    def save_images(
        self,
        images,
        path="",
        filename_prefix="ComfyUI",
        jpg_quality=90,
        prompt=None,
        extra_pnginfo=None,
    ):
        # Combine path and filename_prefix
        if path:
            full_prefix = os.path.join(path, filename_prefix)
        else:
            full_prefix = filename_prefix

        (
            full_output_folder,
            filename,
            counter,
            subfolder,
            _,
        ) = folder_paths.get_save_image_path(
            full_prefix, self.output_dir, images[0].shape[1], images[0].shape[0]
        )

        results = []

        for batch_number, image in enumerate(images):
            # Convert tensor to PIL Image
            i = 255.0 * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

            # Build metadata
            metadata = None
            try:
                from comfy.cli_args import args

                if not args.disable_metadata:
                    metadata = PngInfo()
                    if prompt is not None:
                        metadata.add_text("prompt", json.dumps(prompt))
                    if extra_pnginfo is not None:
                        for x in extra_pnginfo:
                            metadata.add_text(x, json.dumps(extra_pnginfo[x]))
            except Exception:
                # If we can't access args, just skip metadata
                pass

            # Generate filename
            filename_with_batch = filename.replace("%batch_num%", str(batch_number))
            png_file = f"{filename_with_batch}_{counter:05}_.png"
            png_path = os.path.join(full_output_folder, png_file)

            # Save PNG
            img.save(png_path, pnginfo=metadata, compress_level=self.compress_level)

            # Check file size and save JPG if needed
            png_size = os.path.getsize(png_path)
            if png_size > SIZE_THRESHOLD_BYTES:
                jpg_file = f"{filename_with_batch}_{counter:05}_.jpg"
                jpg_path = os.path.join(full_output_folder, jpg_file)
                # Convert to RGB if needed (in case of RGBA)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(jpg_path, quality=jpg_quality, optimize=True)

            results.append({"filename": png_file, "subfolder": subfolder, "type": self.type})
            counter += 1

        return {"ui": {"images": results}}
