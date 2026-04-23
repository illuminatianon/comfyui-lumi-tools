"""Node replacement registrations for Lumi Tools."""

from __future__ import annotations

try:
    from comfy_api.latest import ComfyAPI, io
except ImportError:
    ComfyAPI = None
    io = None


async def register_node_replacements() -> None:
    """Register workflow migration paths for deprecated nodes."""
    if ComfyAPI is None or io is None:
        return

    api = ComfyAPI()

    await api.node_replacement.register(
        io.NodeReplace(
            new_node_id="LumiLLMImagenConfig",
            old_node_id="LumiGeminiImagenConfig",
            old_widget_ids=["aspect_ratio", "image_size", "temperature", "top_p"],
            input_mapping=[
                {"new_id": "config_type", "set_value": "gemini"},
                {"new_id": "aspect_ratio", "old_id": "aspect_ratio"},
                {"new_id": "image_size", "old_id": "image_size"},
                {"new_id": "temperature", "old_id": "temperature"},
                {"new_id": "top_p", "old_id": "top_p"},
            ],
            output_mapping=[{"new_idx": 0, "old_idx": 0}],
        )
    )

    await api.node_replacement.register(
        io.NodeReplace(
            new_node_id="LumiLLMImagenProvider",
            old_node_id="LumiGoogleImagenProvider",
            old_widget_ids=["env_key", "model"],
            input_mapping=[
                {"new_id": "provider_type", "set_value": "google"},
                {"new_id": "env_key", "old_id": "env_key"},
                {"new_id": "model", "old_id": "model"},
            ],
            output_mapping=[{"new_idx": 0, "old_idx": 0}],
        )
    )

    await api.node_replacement.register(
        io.NodeReplace(
            new_node_id="LumiLLMImagenProvider",
            old_node_id="LumiOpenRouterImagenProvider",
            old_widget_ids=["env_key", "model"],
            input_mapping=[
                {"new_id": "provider_type", "set_value": "openrouter"},
                {"new_id": "env_key", "old_id": "env_key"},
                {"new_id": "model", "old_id": "model"},
            ],
            output_mapping=[{"new_idx": 0, "old_idx": 0}],
        )
    )


__all__ = ["register_node_replacements"]
