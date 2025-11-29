from __future__ import annotations

import os
from pathlib import Path

from dynamicprompts.enums import SamplingMethod
from dynamicprompts.sampling_context import SamplingContext
from dynamicprompts.wildcards import WildcardManager

try:
    from server import PromptServer
    HAS_SERVER = True
except ImportError:
    HAS_SERVER = False


# Cache for WildcardManager with mtime-based invalidation
_wildcard_cache: dict = {"manager": None, "mtimes": {}}


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
            folder_paths.folder_names_and_paths["wildcards"] = ([default_path], {".txt", ".yaml", ".json"})

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
        path.mkdir(parents=True, exist_ok=True)
        paths.append(path)

    # Try to use ComfyUI's folder_paths
    try:
        import folder_paths
        for p in folder_paths.get_folder_paths("wildcards"):
            path = Path(p)
            if path.exists() or path == Path(folder_paths.base_path) / "wildcards":
                path.mkdir(parents=True, exist_ok=True)
                if path not in paths:
                    paths.append(path)
    except (ImportError, KeyError):
        pass

    # Also check ./wildcards relative to this node (not recommended, but supported)
    local_path = Path(__file__).parent / "wildcards"
    if local_path.exists() and local_path not in paths:
        paths.append(local_path)

    # Fallback if no paths found
    if not paths:
        fallback = Path("./wildcards")
        fallback.mkdir(parents=True, exist_ok=True)
        paths.append(fallback)

    return paths


# Initialize folder paths on module load
_init_wildcard_folder_paths()


def _get_folder_mtimes(paths: list[Path]) -> dict[Path, float]:
    """
    Get modification times for wildcard folders and their contents.
    Used to detect when wildcards have changed.
    """
    mtimes: dict[Path, float] = {}
    for path in paths:
        if path.exists():
            # Track folder mtime
            mtimes[path] = path.stat().st_mtime
            # Also track individual wildcard files
            for ext in (".txt", ".yaml", ".json"):
                for file in path.rglob(f"*{ext}"):
                    mtimes[file] = file.stat().st_mtime
    return mtimes


def get_wildcard_manager() -> WildcardManager:
    """
    Get a WildcardManager instance with automatic cache invalidation.

    The manager is cached but automatically refreshes when:
    - Wildcard folders are added/removed
    - Wildcard files are added/removed/modified

    Supports multiple wildcard directories via ComfyUI's folder_paths system.
    """
    paths = get_wildcard_paths()
    current_mtimes = _get_folder_mtimes(paths)

    # Check if cache is valid
    if _wildcard_cache["manager"] is not None and _wildcard_cache["mtimes"] == current_mtimes:
        return _wildcard_cache["manager"]

    # Cache miss or invalidated - create new manager
    if len(paths) == 1:
        manager = WildcardManager(path=paths[0])
    else:
        # Multiple paths: use root_map to combine them
        # All paths are mapped to the root "" prefix so wildcards are accessible without prefix
        root_map = {"": paths}
        manager = WildcardManager(root_map=root_map)

    _wildcard_cache["manager"] = manager
    _wildcard_cache["mtimes"] = current_mtimes
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


class LumiWildcardProcessor:

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
                        "wildcard_text": ("STRING", {"multiline": True, "dynamicPrompts": False, "tooltip": "Enter a prompt using wildcard syntax."}),
                        "populated_text": ("STRING", {"multiline": True, "dynamicPrompts": False, "tooltip": "The actual value passed during execution. Wildcard syntax can also be used here."}),
                        "mode": (["populate", "fixed", "reproduce"], {"default": "populate", "tooltip":
                            "populate: Overwrites 'populated_text' with the processed prompt from 'wildcard_text'. Cannot edit 'populated_text' in this mode.\n"
                            "fixed: Ignores wildcard_text and keeps 'populated_text' as is. You can edit 'populated_text' in this mode.\n"
                            "reproduce: Operates as 'fixed' mode once for reproduction, then switches to 'populate' mode."
                            }),
                        "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for wildcard processing."}),
                        "Select to add Wildcard": (get_wildcard_list(),),
                    },
                "hidden": {"unique_id": "UNIQUE_ID"},
                }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Force re-evaluation to refresh wildcard list
        return float("NaN")

    CATEGORY = "Lumi/Prompt"

    DESCRIPTION = "Processes text prompts written in wildcard syntax and outputs the processed text prompt."

    RETURN_TYPES = ("STRING", )
    RETURN_NAMES = ("processed text",)
    FUNCTION = "doit"

    def process(self, text: str, seed: int) -> str:
        context = SamplingContext(
            wildcard_manager=get_wildcard_manager(),
            default_sampling_method=SamplingMethod.RANDOM,
        )
        if seed > 0:
            context.rand.seed(seed)

        prompts = list(context.sample_prompts(text, 1))
        return str(prompts[0]) if prompts else text

    def doit(self, **kwargs):
        mode = kwargs.get('mode', 'populate')
        seed = kwargs['seed']
        unique_id = kwargs.get('unique_id')

        if mode == 'populate':
            # Process wildcard_text and return result
            result = self.process(text=kwargs['wildcard_text'], seed=seed)
        else:
            # fixed/reproduce: use populated_text as-is (but still process any wildcards in it)
            result = self.process(text=kwargs['populated_text'], seed=seed)

        # Send feedback to update the populated_text widget in the UI
        if HAS_SERVER and unique_id is not None:
            PromptServer.instance.send_sync(
                "lumi-node-feedback",
                {"node_id": unique_id, "widget_name": "populated_text", "value": result}
            )

        return (result, )
