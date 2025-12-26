from .nodes import (
    LumiGeminiImagenConfig,
    LumiGoogleImagenProvider,
    LumiLLMImagenProcessor,
    LumiLLMPromptProcessor,
    LumiOpenRouterImagenProvider,
    LumiOpenRouterProvider,
    LumiSaveImage,
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
    "LumiGeminiImagenConfig": LumiGeminiImagenConfig,
    "LumiOpenRouterImagenProvider": LumiOpenRouterImagenProvider,
    "LumiGoogleImagenProvider": LumiGoogleImagenProvider,
    "LumiLLMImagenProcessor": LumiLLMImagenProcessor,
    "LumiSaveImage": LumiSaveImage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LumiSeed": "Lumi Seed",
    "LumiShowText": "Lumi Show Text",
    "LumiShufflePrompt": "Lumi Shuffle Prompt",
    "LumiWildcardProcessor": "Lumi Wildcard Processor",
    "LumiOpenRouterProvider": "Lumi OpenRouter Provider",
    "LumiLLMPromptProcessor": "Lumi LLM Prompt Processor",
    "LumiWrapText": "Lumi Wrap Text",
    "LumiGeminiImagenConfig": "Lumi Gemini Imagen Config",
    "LumiOpenRouterImagenProvider": "Lumi OpenRouter Imagen Provider",
    "LumiGoogleImagenProvider": "Lumi Google Imagen Provider",
    "LumiLLMImagenProcessor": "Lumi LLM Imagen Processor",
    "LumiSaveImage": "Lumi Save Image",
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
