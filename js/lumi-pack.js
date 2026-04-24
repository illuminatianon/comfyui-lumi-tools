import { api } from "../../scripts/api.js";
import { app } from "../../scripts/app.js";

const TIMER_ENABLED_SETTING = "Lumi.InstantRunTimer.Enabled";
const TIMER_MAX_MINUTES_SETTING = "Lumi.InstantRunTimer.MaxMinutes";
const DEFAULT_TIMER_MINUTES = 10;
const MIN_TIMER_MINUTES = 1;
const MAX_TIMER_MINUTES = 240;

const IMAGEN_ASPECT_RATIOS = ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"];
const IMAGEN_RESOLUTIONS = ["1K", "2K", "4K"];
const OPENAI_IMAGE_SIZES = [
    "auto",
    "1024x1024",
    "1536x1024",
    "1024x1536",
    "2048x2048",
    "2048x1152",
    "3840x2160",
    "2160x3840",
];
const OPENAI_QUALITIES = ["auto", "low", "medium", "high"];
const OPENAI_OUTPUT_FORMATS = ["png", "jpeg", "webp"];
const OPENAI_BACKGROUNDS = ["auto", "opaque"];
const IMAGEN_PROVIDER_OPTIONS = {
    google: {
        envKey: "GOOGLE_API_KEY",
        models: [
            "gemini-3-pro-image-preview",
            "gemini-3.1-flash-image-preview",
            "gemini-2.5-flash-image",
        ],
    },
    openrouter: {
        envKey: "OPENROUTER_API_KEY",
        models: [
            "google/gemini-2.0-flash-preview-image-generation",
            "google/gemini-3-pro-image-preview",
            "google/gemini-3.1-flash-image-preview",
            "google/gemini-2.5-flash-image",
        ],
    },
    openai: {
        envKey: "OPENAI_API_KEY",
        models: ["gpt-image-2", "gpt-image-1"],
    },
};

const IMAGEN_CONFIG_WIDGETS = [
    "aspect_ratio",
    "image_size",
    "temperature",
    "top_p",
    "size_mode",
    "size_preset",
    "size_custom",
    "quality",
    "output_format",
    "background",
];
const IMAGEN_PROVIDER_WIDGETS = ["env_key", "model"];

const timerState = {
    enabled: false,
    maxMinutes: DEFAULT_TIMER_MINUTES,
    remainingMs: DEFAULT_TIMER_MINUTES * 60 * 1000,
    wasInstantRunning: false,
    lastTickAt: 0,
    intervalId: null,
};

function extensionManager() {
    return app.extensionManager ?? null;
}

function getSetting(key, fallbackValue) {
    const manager = extensionManager();
    if (!manager?.setting) {
        return fallbackValue;
    }

    const value = manager.setting.get(key);
    return value ?? fallbackValue;
}

function setSetting(key, value) {
    const manager = extensionManager();
    if (!manager?.setting) {
        return;
    }

    manager.setting.set(key, value);
}

function notify(summary, detail, severity = "info") {
    const manager = extensionManager();
    if (manager?.toast?.add) {
        manager.toast.add({
            severity,
            summary,
            detail,
            life: 3200,
        });
        return;
    }

    console.log(`[Lumi Instant Timer] ${summary}: ${detail}`);
}

function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
}

function formatRemaining(ms) {
    const totalSeconds = Math.max(0, Math.ceil(ms / 1000));
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

function resetTimer() {
    timerState.remainingMs = timerState.maxMinutes * 60 * 1000;
}

function loadTimerSettings() {
    timerState.enabled = Boolean(getSetting(TIMER_ENABLED_SETTING, false));

    const parsedMinutes = Number(getSetting(TIMER_MAX_MINUTES_SETTING, DEFAULT_TIMER_MINUTES));
    timerState.maxMinutes = Number.isFinite(parsedMinutes)
        ? clamp(Math.round(parsedMinutes), MIN_TIMER_MINUTES, MAX_TIMER_MINUTES)
        : DEFAULT_TIMER_MINUTES;

    setSetting(TIMER_MAX_MINUTES_SETTING, timerState.maxMinutes);
    resetTimer();
}

function isInstantRunActive() {
    const modernRunButton = document.querySelector("[data-testid='queue-button']");
    if (modernRunButton) {
        return modernRunButton.getAttribute("data-variant") === "destructive";
    }

    return Boolean(app.ui?.autoQueueEnabled && app.ui?.autoQueueMode === "instant");
}

function stopInstantRun() {
    const modernRunButton = document.querySelector("[data-testid='queue-button']");
    if (modernRunButton && modernRunButton.getAttribute("data-variant") === "destructive") {
        modernRunButton.click();
        return true;
    }

    if (app.ui) {
        app.ui.autoQueueEnabled = false;
        if (app.ui.autoQueueMode === "instant") {
            app.ui.autoQueueMode = "change";
        }

        const autoQueueCheckbox = document.getElementById("autoQueueCheckbox");
        if (autoQueueCheckbox && "checked" in autoQueueCheckbox) {
            autoQueueCheckbox.checked = false;
        }
        return true;
    }

    return false;
}

function setTimerEnabled(enabled) {
    timerState.enabled = enabled;
    setSetting(TIMER_ENABLED_SETTING, enabled);
    timerState.wasInstantRunning = false;
    timerState.lastTickAt = Date.now();
    resetTimer();
}

function handleTimerExpiration() {
    const didStop = stopInstantRun();
    resetTimer();
    timerState.wasInstantRunning = false;

    notify(
        "Instant timer finished",
        didStop
            ? `Stopped Run (Instant) after ${timerState.maxMinutes} minute(s).`
            : "Timer reached 0, but no running instant mode was detected.",
        didStop ? "warn" : "info"
    );
}

function tickInstantTimer() {
    const now = Date.now();
    const isRunning = isInstantRunActive();

    if (!timerState.enabled) {
        timerState.wasInstantRunning = isRunning;
        timerState.lastTickAt = now;
        resetTimer();
        return;
    }

    if (isRunning && !timerState.wasInstantRunning) {
        resetTimer();
        timerState.wasInstantRunning = true;
        timerState.lastTickAt = now;
        return;
    }

    if (!isRunning) {
        if (timerState.wasInstantRunning) {
            resetTimer();
        }
        timerState.wasInstantRunning = false;
        timerState.lastTickAt = now;
        return;
    }

    const deltaMs = now - timerState.lastTickAt;
    timerState.lastTickAt = now;
    timerState.remainingMs -= deltaMs;

    if (timerState.remainingMs <= 0) {
        handleTimerExpiration();
    }
}

function startTimerWatcher() {
    if (timerState.intervalId !== null) {
        return;
    }

    timerState.lastTickAt = Date.now();
    timerState.intervalId = window.setInterval(tickInstantTimer, 1000);
}

function configureTimerMinutes() {
    const answer = window.prompt(
        `Max Run (Instant) minutes (${MIN_TIMER_MINUTES}-${MAX_TIMER_MINUTES})`,
        String(timerState.maxMinutes)
    );

    if (answer === null) {
        return;
    }

    const parsed = Number(answer);
    if (!Number.isFinite(parsed)) {
        notify("Invalid value", "Please enter a valid number of minutes.", "error");
        return;
    }

    timerState.maxMinutes = clamp(Math.round(parsed), MIN_TIMER_MINUTES, MAX_TIMER_MINUTES);
    setSetting(TIMER_MAX_MINUTES_SETTING, timerState.maxMinutes);
    resetTimer();

    notify(
        "Instant timer updated",
        `Maximum Run (Instant) duration is now ${timerState.maxMinutes} minute(s).`
    );
}

function timerToggleLabel() {
    if (!timerState.enabled) {
        return "Enable Instant Timer";
    }

    const status = timerState.wasInstantRunning
        ? `Running ${formatRemaining(timerState.remainingMs)}`
        : "Waiting";
    return `Disable Instant Timer (${status})`;
}

// Handle feedback from Python to update widget values
function nodeFeedbackHandler(event) {
    const nodes = app.graph._nodes_by_id;
    const node = nodes[event.detail.node_id];
    if (node) {
        const widget = node.widgets.find((w) => event.detail.widget_name === w.name);
        if (widget) {
            widget.value = event.detail.value;
        }
    }
}

api.addEventListener("lumi-node-feedback", nodeFeedbackHandler);

const extension = {
    name: "Comfy.LumiPack",

    settings: [
        {
            id: TIMER_ENABLED_SETTING,
            category: ["Lumi", "Run", "Instant Timer"],
            name: "Enable max duration guard",
            tooltip: "When enabled, Run (Instant) is automatically stopped after the configured time.",
            type: "boolean",
            defaultValue: false,
        },
        {
            id: TIMER_MAX_MINUTES_SETTING,
            category: ["Lumi", "Run", "Instant Timer"],
            name: "Maximum Run (Instant) minutes",
            tooltip: "Maximum time Run (Instant) is allowed to keep auto-queueing.",
            type: "slider",
            attrs: {
                min: MIN_TIMER_MINUTES,
                max: MAX_TIMER_MINUTES,
                step: 1,
            },
            defaultValue: DEFAULT_TIMER_MINUTES,
        },
    ],

    commands: [
        {
            id: "Lumi.InstantTimer.Toggle",
            label: timerToggleLabel,
            menubarLabel: timerToggleLabel,
            function: () => {
                const nextEnabled = !timerState.enabled;
                setTimerEnabled(nextEnabled);
                notify(
                    nextEnabled ? "Instant timer enabled" : "Instant timer disabled",
                    nextEnabled
                        ? `Run (Instant) will stop after ${timerState.maxMinutes} minute(s).`
                        : "Timer disabled and reset."
                );
            },
            active: () => timerState.enabled,
        },
        {
            id: "Lumi.InstantTimer.ConfigureMinutes",
            label: "Set Instant Timer Minutes",
            menubarLabel: "Set Instant Timer Minutes",
            function: configureTimerMinutes,
        },
    ],

    menuCommands: [
        {
            path: ["Run"],
            commands: ["Lumi.InstantTimer.Toggle", "Lumi.InstantTimer.ConfigureMinutes"],
        },
    ],

    async setup() {
        loadTimerSettings();
        startTimerWatcher();
        tickInstantTimer();
        return undefined;
    },

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "LumiWildcardProcessor") {
            setupWildcardProcessorNode(nodeType, nodeData);
        } else if (nodeData.name === "LumiWildcardEncode") {
            setupWildcardEncodeNode(nodeType, nodeData);
        } else if (nodeData.name === "LumiLLMImagenConfig") {
            setupLLMImagenConfigNode(nodeType, nodeData);
        } else if (nodeData.name === "LumiLLMImagenProvider") {
            setupLLMImagenProviderNode(nodeType, nodeData);
        }
    }
};

app.registerExtension(extension);

function widgetValue(node, name, fallbackValue) {
    const widget = node.widgets?.find((w) => w.name === name);
    return widget?.value ?? fallbackValue;
}

function removeWidgets(node, names) {
    if (!node.widgets) {
        return;
    }

    node.widgets = node.widgets.filter((widget) => !names.includes(widget.name));
}

function addSerializedWidget(node, type, name, value, callback, options = {}) {
    const widget = node.addWidget(type, name, value, callback, options);
    widget.serialize = true;
    return widget;
}

function refreshNodeSize(node) {
    if (node.computeSize && node.setSize) {
        node.setSize(node.computeSize());
    }
    app.graph?.setDirtyCanvas(true, true);
}

function setupLLMImagenConfigNode(nodeType, nodeData) {
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    const onConfigure = nodeType.prototype.onConfigure;

    nodeType.prototype.onConfigure = function () {
        if (onConfigure) {
            onConfigure.apply(this, arguments);
        }
        this.updateLumiImagenConfigWidgets?.();
    };

    nodeType.prototype.onNodeCreated = function () {
        if (onNodeCreated) {
            onNodeCreated.apply(this, arguments);
        }

        const configTypeWidget = this.widgets.find((w) => w.name === "config_type");
        const updateWidgets = () => {
            for (const widget of this.widgets ?? []) {
                if (widget.name && ["config_type", ...IMAGEN_CONFIG_WIDGETS].includes(widget.name)) {
                    widget.serialize = true;
                }
            }

            refreshNodeSize(this);
        };

        if (configTypeWidget) {
            const originalCallback = configTypeWidget.callback;
            configTypeWidget.callback = function (value) {
                if (originalCallback) {
                    originalCallback.apply(this, arguments);
                }
                updateWidgets(value);
            };
        }

        this.updateLumiImagenConfigWidgets = updateWidgets;
        updateWidgets();
    };
}

function setupLLMImagenProviderNode(nodeType, nodeData) {
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    const onConfigure = nodeType.prototype.onConfigure;

    nodeType.prototype.onConfigure = function () {
        if (onConfigure) {
            onConfigure.apply(this, arguments);
        }
        this.updateLumiImagenProviderWidgets?.();
    };

    nodeType.prototype.onNodeCreated = function () {
        if (onNodeCreated) {
            onNodeCreated.apply(this, arguments);
        }

        const providerTypeWidget = this.widgets.find((w) => w.name === "provider_type");
        const updateWidgets = () => {
            const providerType = providerTypeWidget?.value ?? "google";
            const providerOptions = IMAGEN_PROVIDER_OPTIONS[providerType] ?? IMAGEN_PROVIDER_OPTIONS.google;
            const existingEnvKey = widgetValue(this, "env_key", providerOptions.envKey);
            const defaultEnvKeys = Object.values(IMAGEN_PROVIDER_OPTIONS).map((options) => options.envKey);
            const envKey = defaultEnvKeys.includes(existingEnvKey) ? providerOptions.envKey : existingEnvKey;
            const previousModel = widgetValue(this, "model", providerOptions.models[0]);
            const model = providerOptions.models.includes(previousModel)
                ? previousModel
                : providerOptions.models[0];

            removeWidgets(this, IMAGEN_PROVIDER_WIDGETS);
            addSerializedWidget(this, "text", "env_key", envKey, undefined, {});
            addSerializedWidget(this, "combo", "model", model, undefined, {
                values: providerOptions.models,
            });

            refreshNodeSize(this);
        };

        if (providerTypeWidget) {
            const originalCallback = providerTypeWidget.callback;
            providerTypeWidget.callback = function (value) {
                if (originalCallback) {
                    originalCallback.apply(this, arguments);
                }
                updateWidgets(value);
            };
        }

        this.updateLumiImagenProviderWidgets = updateWidgets;
        updateWidgets();
    };
}

function setupWildcardProcessorNode(nodeType, nodeData) {
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
        if (onNodeCreated) {
            onNodeCreated.apply(this, arguments);
        }

        const wildcardTextWidget = this.widgets.find((w) => w.name === "wildcard_text");
        const populatedTextWidget = this.widgets.find((w) => w.name === "populated_text");
        const modeWidget = this.widgets.find((w) => w.name === "mode");
        const selectWildcardWidget = this.widgets.find((w) => w.name === "Select to add Wildcard");

        // Set placeholders
        if (wildcardTextWidget?.inputEl) {
            wildcardTextWidget.inputEl.placeholder = "Wildcard Prompt (e.g., __colors__ cat)";
        }
        if (populatedTextWidget?.inputEl) {
            populatedTextWidget.inputEl.placeholder = "Populated Prompt (auto-generated)";
        }

        // Disable populated_text in populate mode
        const updatePopulatedState = () => {
            if (populatedTextWidget?.inputEl) {
                populatedTextWidget.inputEl.disabled = modeWidget?.value === "populate";
            }
        };

        if (modeWidget) {
            const originalCallback = modeWidget.callback;
            modeWidget.callback = function (value) {
                if (originalCallback) {
                    originalCallback.apply(this, arguments);
                }
                updatePopulatedState();
            };
        }

        // Initial state
        updatePopulatedState();

        // Handle wildcard selection - append to wildcard_text
        if (selectWildcardWidget) {
            selectWildcardWidget.callback = (value) => {
                if (value && !value.startsWith("Select")) {
                    if (wildcardTextWidget) {
                        if (wildcardTextWidget.value && wildcardTextWidget.value.trim() !== "") {
                            wildcardTextWidget.value += " " + value;
                        } else {
                            wildcardTextWidget.value = value;
                        }
                    }
                }
            };

            // Reset dropdown display after selection
            Object.defineProperty(selectWildcardWidget, "value", {
                set: function (v) {
                    if (v && !v.startsWith("Select")) {
                        this._value = v;
                    }
                },
                get: function () {
                    return "Select the Wildcard to add to the text";
                }
            });
        }
    };
}

function setupWildcardEncodeNode(nodeType, nodeData) {
    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
        if (onNodeCreated) {
            onNodeCreated.apply(this, arguments);
        }

        const wildcardTextWidget = this.widgets.find((w) => w.name === "wildcard_text");
        const populatedTextWidget = this.widgets.find((w) => w.name === "populated_text");
        const modeWidget = this.widgets.find((w) => w.name === "mode");
        const selectLoraWidget = this.widgets.find((w) => w.name === "Select to add LoRA");
        const selectWildcardWidget = this.widgets.find((w) => w.name === "Select to add Wildcard");

        // Set placeholders
        if (wildcardTextWidget?.inputEl) {
            wildcardTextWidget.inputEl.placeholder = "Wildcard Prompt with LoRA support\ne.g., __colors__ cat <lora:detail:0.8>";
        }
        if (populatedTextWidget?.inputEl) {
            populatedTextWidget.inputEl.placeholder = "Populated Prompt (auto-generated)";
        }

        // Disable populated_text in populate mode
        const updatePopulatedState = () => {
            if (populatedTextWidget?.inputEl) {
                populatedTextWidget.inputEl.disabled = modeWidget?.value === "populate";
            }
        };

        if (modeWidget) {
            const originalCallback = modeWidget.callback;
            modeWidget.callback = function (value) {
                if (originalCallback) {
                    originalCallback.apply(this, arguments);
                }
                updatePopulatedState();
            };
        }

        updatePopulatedState();

        // Handle LoRA selection - append to wildcard_text
        if (selectLoraWidget) {
            selectLoraWidget.callback = (value) => {
                if (value && !value.startsWith("Select")) {
                    if (wildcardTextWidget) {
                        const loraTag = `<lora:${value}:1>`;
                        if (wildcardTextWidget.value && wildcardTextWidget.value.trim() !== "") {
                            wildcardTextWidget.value += " " + loraTag;
                        } else {
                            wildcardTextWidget.value = loraTag;
                        }
                    }
                }
            };

            Object.defineProperty(selectLoraWidget, "value", {
                set: function (v) {
                    if (v && !v.startsWith("Select")) {
                        this._value = v;
                    }
                },
                get: function () {
                    return "Select the LoRA to add to the text";
                }
            });
        }

        // Handle wildcard selection - append to wildcard_text
        if (selectWildcardWidget) {
            selectWildcardWidget.callback = (value) => {
                if (value && !value.startsWith("Select")) {
                    if (wildcardTextWidget) {
                        if (wildcardTextWidget.value && wildcardTextWidget.value.trim() !== "") {
                            wildcardTextWidget.value += " " + value;
                        } else {
                            wildcardTextWidget.value = value;
                        }
                    }
                }
            };

            Object.defineProperty(selectWildcardWidget, "value", {
                set: function (v) {
                    if (v && !v.startsWith("Select")) {
                        this._value = v;
                    }
                },
                get: function () {
                    return "Select the Wildcard to add to the text";
                }
            });
        }
    };
}
