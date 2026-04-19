from .nodes import (
    LumiGeminiImagenConfig,
    LumiGoogleImagenProvider,
    LumiLLMImagenProcessor,
    LumiLLMPromptProcessor,
    LumiLoadImage,
    LumiNoiseToSeed,
    LumiOpenRouterImagenProvider,
    LumiOpenRouterProvider,
    LumiSaveImage,
    LumiSeed,
    LumiShowText,
    LumiShufflePrompt,
    LumiTextInput,
    LumiWildcardProcessor,
    LumiWrapText,
)

try:
    from comfy_api.latest import ComfyExtension, io
except ImportError:
    ComfyExtension = None
    io = None

NODE_CLASS_MAPPINGS = {
    "LumiNoiseToSeed": LumiNoiseToSeed,
    "LumiSeed": LumiSeed,
    "LumiShowText": LumiShowText,
    "LumiShufflePrompt": LumiShufflePrompt,
    "LumiTextInput": LumiTextInput,
    "LumiWildcardProcessor": LumiWildcardProcessor,
    "LumiOpenRouterProvider": LumiOpenRouterProvider,
    "LumiLLMPromptProcessor": LumiLLMPromptProcessor,
    "LumiWrapText": LumiWrapText,
    "LumiGeminiImagenConfig": LumiGeminiImagenConfig,
    "LumiOpenRouterImagenProvider": LumiOpenRouterImagenProvider,
    "LumiGoogleImagenProvider": LumiGoogleImagenProvider,
    "LumiLLMImagenProcessor": LumiLLMImagenProcessor,
    "LumiLoadImage": LumiLoadImage,
    "LumiSaveImage": LumiSaveImage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LumiNoiseToSeed": "Lumi Noise To Seed",
    "LumiSeed": "Lumi Seed",
    "LumiShowText": "Lumi Show Text",
    "LumiShufflePrompt": "Lumi Shuffle Prompt",
    "LumiTextInput": "Lumi Text Input",
    "LumiWildcardProcessor": "Lumi Wildcard Processor",
    "LumiOpenRouterProvider": "Lumi OpenRouter Provider",
    "LumiLLMPromptProcessor": "Lumi LLM Prompt Processor",
    "LumiWrapText": "Lumi Wrap Text",
    "LumiGeminiImagenConfig": "Lumi Gemini Imagen Config",
    "LumiOpenRouterImagenProvider": "Lumi OpenRouter Imagen Provider",
    "LumiGoogleImagenProvider": "Lumi Google Imagen Provider",
    "LumiLLMImagenProcessor": "Lumi LLM Imagen Processor",
    "LumiLoadImage": "Lumi Load Image",
    "LumiSaveImage": "Lumi Save Image",
}

WEB_DIRECTORY = "./js"

if ComfyExtension is not None:

    class LumiToolsV3Extension(ComfyExtension):
        async def get_node_list(self) -> list[type[io.ComfyNode]]:
            return [
                LumiNoiseToSeed,
                LumiSeed,
                LumiTextInput,
                LumiWrapText,
                LumiShufflePrompt,
                LumiOpenRouterProvider,
                LumiGeminiImagenConfig,
                LumiOpenRouterImagenProvider,
                LumiGoogleImagenProvider,
                LumiLLMPromptProcessor,
                LumiLLMImagenProcessor,
                LumiLoadImage,
                LumiSaveImage,
                LumiShowText,
                LumiWildcardProcessor,
            ]

    async def comfy_entrypoint() -> ComfyExtension:
        return LumiToolsV3Extension()


__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
if ComfyExtension is not None:
    __all__.append("comfy_entrypoint")
