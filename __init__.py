from .nodes import LumiWildcardProcessor, LumiWildcardEncode

NODE_CLASS_MAPPINGS = {
    "LumiWildcardProcessor": LumiWildcardProcessor,
    "LumiWildcardEncode": LumiWildcardEncode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LumiWildcardProcessor": "Lumi Wildcard Processor",
    "LumiWildcardEncode": "Lumi Wildcard Encode",
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
