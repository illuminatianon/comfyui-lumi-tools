from .main import LumiWildcardProcessor

NODE_CLASS_MAPPINGS = {
    "LumiWildcardProcessor": LumiWildcardProcessor,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LumiWildcardProcessor": "Lumi Wildcard Processor",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

