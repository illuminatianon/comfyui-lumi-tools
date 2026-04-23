"""Shared custom V3 types for Lumi nodes."""

from __future__ import annotations

try:
    from comfy_api.latest import io
except ImportError:
    io = None


if io is not None:
    LLM_PROVIDER_TYPE = io.Custom("LLM_PROVIDER")
    IMAGEN_PROVIDER_TYPE = io.Custom("IMAGEN_PROVIDER")
    IMAGEN_CONFIG_TYPE = io.Custom("IMAGEN_CONFIG")
    LUMI_IMAGE_CHAIN_TYPE = io.Custom("LUMI_IMAGE_CHAIN")
else:
    LLM_PROVIDER_TYPE = None
    IMAGEN_PROVIDER_TYPE = None
    IMAGEN_CONFIG_TYPE = None
    LUMI_IMAGE_CHAIN_TYPE = None


__all__ = [
    "LLM_PROVIDER_TYPE",
    "IMAGEN_PROVIDER_TYPE",
    "IMAGEN_CONFIG_TYPE",
    "LUMI_IMAGE_CHAIN_TYPE",
]
