from .main import LumiWildcardProcessor

NODE_CLASS_MAPPINGS = {
    "LumiWildcardProcessor": LumiWildcardProcessor,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LumiWildcardProcessor": "Lumi Wildcard Processor",
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

