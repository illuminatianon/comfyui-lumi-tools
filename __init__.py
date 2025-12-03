from .nodes import LumiWildcardProcessor, LumiWildcardEncode, LumiShowText, LumiShufflePrompt

NODE_CLASS_MAPPINGS = {
    "LumiWildcardProcessor": LumiWildcardProcessor,
    "LumiWildcardEncode": LumiWildcardEncode,
    "LumiShowText": LumiShowText,
    "LumiShufflePrompt": LumiShufflePrompt,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LumiWildcardProcessor": "Lumi Wildcard Processor",
    "LumiWildcardEncode": "Lumi Wildcard Encode",
    "LumiShowText": "Lumi Show Text",
    "LumiShufflePrompt": "Lumi Shuffle Prompt",
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
