"""
Shared wildcard utilities for Lumi Pack nodes.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from dynamicprompts.enums import SamplingMethod
from dynamicprompts.sampling_context import SamplingContext
from dynamicprompts.wildcards import WildcardManager

logger = logging.getLogger(__name__)
_CACHE_VALIDATION_INTERVAL = float(os.environ.get("LUMI_WILDCARDS_CACHE_INTERVAL", "30"))
_WILDCARD_EXTENSIONS = (".txt", ".yaml", ".json")
_wildcard_cache: dict = {"manager": None, "paths": (), "snapshot": None, "validated_at": 0.0}


def _init_wildcard_folder_paths() -> None:
    """
    Register 'wildcards' as a folder type in ComfyUI's folder_paths.
    This allows users to add custom wildcard paths via extra_model_paths.yaml
    """
    try:
        import folder_paths

        # Register default wildcards path if not already registered
        if "wildcards" not in folder_paths.folder_names_and_paths:
            default_path = os.path.join(folder_paths.base_path, "wildcards")
            folder_paths.folder_names_and_paths["wildcards"] = (
                [default_path],
                {".txt", ".yaml", ".json"},
            )

            # Create the default folder if it doesn't exist
            os.makedirs(default_path, exist_ok=True)
    except ImportError:
        pass


def get_wildcard_paths() -> list[Path]:
    """
    Get all configured wildcard paths.

    Priority:
    1. LUMI_WILDCARDS_PATH environment variable (if set, adds to the list)
    2. All paths from folder_paths "wildcards" (configurable via extra_model_paths.yaml)
    3. ./wildcards (fallback if nothing else works)

    To add custom paths, edit ComfyUI/extra_model_paths.yaml:

        my_wildcards:
            wildcards: D:/dev/wildcards

    Or on Linux:

        my_wildcards:
            wildcards: /home/user/my/wildcards/folder
    """
    paths: list[Path] = []

    # Check environment variable
    env_path = os.environ.get("LUMI_WILDCARDS_PATH")
    if env_path:
        path = Path(env_path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        paths.append(path)

    # Try to use ComfyUI's folder_paths
    try:
        import folder_paths

        for p in folder_paths.get_folder_paths("wildcards"):
            path = Path(p)
            exists = path.exists()
            if exists or path == Path(folder_paths.base_path) / "wildcards":
                if not exists:
                    path.mkdir(parents=True, exist_ok=True)
                if path not in paths:
                    paths.append(path)
    except (ImportError, KeyError):
        pass

    # Also check ./wildcards relative to this node pack (not recommended, but supported)
    local_path = Path(__file__).parent.parent / "wildcards"
    if local_path.exists() and local_path not in paths:
        paths.append(local_path)

    # Fallback if no paths found
    if not paths:
        fallback = Path("./wildcards")
        if not fallback.exists():
            fallback.mkdir(parents=True, exist_ok=True)
        paths.append(fallback)

    return paths


# Initialize folder paths on module load
_init_wildcard_folder_paths()


def _scan_wildcards(paths: list[Path]) -> tuple[set[str], dict[str, tuple[int, int, int]]]:
    """Track directories and wildcard file metadata in one walk per root."""
    started = time.monotonic()
    directories: set[str] = set()
    files: dict[str, tuple[int, int, int]] = {}
    for path in paths:
        for directory, _, names in os.walk(path):
            directories.add(directory)
            for name in names:
                if not name.endswith(_WILDCARD_EXTENSIONS):
                    continue
                file = os.path.join(directory, name)
                stat = os.stat(file)
                files[file] = (stat.st_mtime_ns, stat.st_ctime_ns, stat.st_size)
    logger.debug("Wildcard filesystem scan took %.3f s", time.monotonic() - started)
    return directories, files


def get_wildcard_manager() -> WildcardManager:
    """
    Get a WildcardManager instance with automatic cache invalidation.

    The manager is cached but automatically refreshes when:
    - Wildcard folders are added/removed
    - Wildcard files are added/removed/modified

    Supports multiple wildcard directories via ComfyUI's folder_paths system.
    """
    manager = _wildcard_cache["manager"]
    now = time.monotonic()
    if manager is not None and now - _wildcard_cache["validated_at"] < _CACHE_VALIDATION_INTERVAL:
        return manager

    paths = get_wildcard_paths()
    snapshot = _scan_wildcards(paths)
    if (
        manager is not None
        and _wildcard_cache["paths"] == tuple(paths)
        and _wildcard_cache["snapshot"] == snapshot
    ):
        _wildcard_cache["validated_at"] = time.monotonic()
        return manager

    started = time.monotonic()
    if len(paths) == 1:
        manager = WildcardManager(path=paths[0])
    else:
        # Map every root to the same prefix for unprefixed wildcard names.
        manager = WildcardManager(root_map={"": paths})

    logger.debug("Wildcard manager initialization/reload took %.3f s", time.monotonic() - started)
    _wildcard_cache["manager"] = manager
    _wildcard_cache["paths"] = tuple(paths)
    _wildcard_cache["snapshot"] = snapshot
    _wildcard_cache["validated_at"] = time.monotonic()
    return manager


def get_wildcard_list() -> list[str]:
    """Get a sorted list of available wildcards formatted for the dropdown."""
    try:
        wm = get_wildcard_manager()
        names = sorted(wm.get_collection_names())
        # Format as __wildcard__ for easy copy-paste
        return ["Select the Wildcard to add to the text"] + [f"__{name}__" for name in names]
    except Exception:
        return ["Select the Wildcard to add to the text"]


def process_wildcards(text: str, seed: int) -> str:
    """
    Process a text string containing wildcard syntax and return the resolved text.

    Args:
        text: The text containing wildcard syntax (e.g., "__colors__ cat")
        seed: Random seed for reproducible wildcard resolution

    Returns:
        The processed text with wildcards resolved
    """
    context = SamplingContext(
        wildcard_manager=get_wildcard_manager(),
        default_sampling_method=SamplingMethod.RANDOM,
    )
    if seed > 0:
        context.rand.seed(seed)

    prompts = list(context.sample_prompts(text, 1))
    return str(prompts[0]) if prompts else text
