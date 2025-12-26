# LLM Prompt Processor

We're going to build our own LLMPromptProcessor nodes. Crucially, we want the provider to be a separate node routed into the processor. these provider nodes (we're starting with OpenRouter) will configure the API Key via customizable ENV_KEY (with certain defaults, OPENROUTER_API_KEY, etc). It will also select the model, and configure max_tokens and top_p.

The actual LLMPromptProcessor will accept Instructions, Prompt, and Seed and output the resulting text.

The basic idea is for the LLMPromptProcessor to be as stateless as possible. The provider node will manage the state and configuration.
We must ensure that API keys are not exposed in the UI or in the workflow/prompt (as written to output files).

For the list of models, we will query openrouter.ai/api/v1/models at startup and cache the result. Providers can use this list to select the model as needed.

Inference will be done with using requests and REST APIs. We will not use any provider-specific libraries.
