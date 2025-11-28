from dynamicprompts.generators import RandomPromptGenerator


class LumiWildcardProcessor:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
                        "wildcard_text": ("STRING", {"multiline": True, "dynamicPrompts": False, "tooltip": "Enter a prompt using wildcard syntax."}),
                        "populated_text": ("STRING", {"multiline": True, "dynamicPrompts": False, "tooltip": "The actual value passed during execution. Wildcard syntax can also be used here."}),
                        "mode": (["populate", "fixed", "reproduce"], {"default": "populate", "tooltip":
                            "populate: Overwrites 'populated_text' with the processed prompt from 'wildcard_text'. Cannot edit 'populated_text' in this mode.\n"
                            "fixed: Ignores wildcard_text and keeps 'populated_text' as is. You can edit 'populated_text' in this mode.\n"
                            "reproduce: Operates as 'fixed' mode once for reproduction, then switches to 'populate' mode."
                            }),
                        "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "tooltip": "Random seed for wildcard processing."}),
                        "Select to add Wildcard": (["Select the Wildcard to add to the text"],),
                    },
                }

    CATEGORY = "Lumi/Prompt"

    DESCRIPTION = "Processes text prompts written in wildcard syntax and outputs the processed text prompt."

    RETURN_TYPES = ("STRING", )
    RETURN_NAMES = ("processed text",)
    FUNCTION = "doit"

    @staticmethod
    def process(text: str, seed: int) -> str:
        generator = RandomPromptGenerator(seed=seed)
        results = generator.generate(text, num_images=1)
        return results[0] if results else text

    def doit(self, *args, **kwargs):
        populated_text = LumiWildcardProcessor.process(text=kwargs['populated_text'], seed=kwargs['seed'])
        return (populated_text, )
