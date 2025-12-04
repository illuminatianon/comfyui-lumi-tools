from .nodes import (
    LumiShowText,
    LumiShufflePrompt,
    LumiWildcardProcessor,
)

NODE_CLASS_MAPPINGS = {
    "LumiWildcardProcessor": LumiWildcardProcessor,
    "LumiShowText": LumiShowText,
    "LumiShufflePrompt": LumiShufflePrompt,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LumiWildcardProcessor": "Lumi Wildcard Processor",
    "LumiShowText": "Lumi Show Text",
    "LumiShufflePrompt": "Lumi Shuffle Prompt",
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
