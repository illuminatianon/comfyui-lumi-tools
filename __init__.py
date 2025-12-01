from .nodes import LumiWildcardProcessor, LumiWildcardEncode, LumiShowText

NODE_CLASS_MAPPINGS = {
    "LumiWildcardProcessor": LumiWildcardProcessor,
    "LumiWildcardEncode": LumiWildcardEncode,
    "LumiShowText": LumiShowText,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LumiWildcardProcessor": "Lumi Wildcard Processor",
    "LumiWildcardEncode": "Lumi Wildcard Encode",
    "LumiShowText": "Lumi Show Text",
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
