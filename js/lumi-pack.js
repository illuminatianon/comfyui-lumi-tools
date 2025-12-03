import { api } from "../../scripts/api.js";
import { app } from "../../scripts/app.js";

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

app.registerExtension({
    name: "Comfy.LumiPack",

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "LumiWildcardProcessor") {
            setupWildcardProcessorNode(nodeType, nodeData);
        } else if (nodeData.name === "LumiWildcardEncode") {
            setupWildcardEncodeNode(nodeType, nodeData);
        }
    }
});

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



