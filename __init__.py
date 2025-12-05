from .nodes import (
    LumiSeed,
    LumiShowText,
    LumiShufflePrompt,
    LumiWildcardProcessor,
)

NODE_CLASS_MAPPINGS = {
    "LumiSeed": LumiSeed,
    "LumiShowText": LumiShowText,
    "LumiShufflePrompt": LumiShufflePrompt,
    "LumiWildcardProcessor": LumiWildcardProcessor,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LumiSeed": "Lumi Seed",
    "LumiShowText": "Lumi Show Text",
    "LumiShufflePrompt": "Lumi Shuffle Prompt",
    "LumiWildcardProcessor": "Lumi Wildcard Processor",
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
