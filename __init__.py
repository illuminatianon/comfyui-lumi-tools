from .nodes import (
    LumiLLMPromptProcessor,
    LumiOpenRouterProvider,
    LumiSeed,
    LumiShowText,
    LumiShufflePrompt,
    LumiWildcardProcessor,
    LumiWrapText,
)

NODE_CLASS_MAPPINGS = {
    "LumiSeed": LumiSeed,
    "LumiShowText": LumiShowText,
    "LumiShufflePrompt": LumiShufflePrompt,
    "LumiWildcardProcessor": LumiWildcardProcessor,
    "LumiOpenRouterProvider": LumiOpenRouterProvider,
    "LumiLLMPromptProcessor": LumiLLMPromptProcessor,
    "LumiWrapText": LumiWrapText,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LumiSeed": "Lumi Seed",
    "LumiShowText": "Lumi Show Text",
    "LumiShufflePrompt": "Lumi Shuffle Prompt",
    "LumiWildcardProcessor": "Lumi Wildcard Processor",
    "LumiOpenRouterProvider": "Lumi OpenRouter Provider",
    "LumiLLMPromptProcessor": "Lumi LLM Prompt Processor",
    "LumiWrapText": "Lumi Wrap Text",
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
