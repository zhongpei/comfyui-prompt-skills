/**
 * ComfyUI Extension: Prompt Skills Vue Container
 * 
 * This extension hijacks the OpencodeContainerNode DOM to mount the
 * Vue.js application. It follows the Frontend V2 standard using
 * app.registerExtension.
 */

import { app } from "/scripts/app.js";

// Dynamic import of Vue app (will be built by Vite)
let mountApp = null;

async function loadVueApp() {
    if (mountApp) return mountApp;

    try {
        // Try to load the built Vue module
        const module = await import("./prompt-skills.es.js");
        mountApp = module.mountApp;
        return mountApp;
    } catch (e) {
        console.warn("Prompt Skills: Vue app not built. Run 'npm run build' in web/");
        return null;
    }
}

app.registerExtension({
    name: "PromptSkills.VueContainer",

    async setup() {
        console.log("Prompt Skills: Extension loaded");
    },

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name !== "OpencodeContainerNode") return;

        // Store original onNodeCreated
        const onNodeCreated = nodeType.prototype.onNodeCreated;

        nodeType.prototype.onNodeCreated = async function () {
            // Call original if exists
            if (onNodeCreated) {
                onNodeCreated.apply(this);
            }

            const node = this;

            // Create container for Vue app
            const container = document.createElement("div");
            container.id = `prompt-skills-${node.id}`;
            container.style.cssText = `
                width: 100%;
                min-height: 300px;
                overflow: hidden;
            `;

            // Add as DOM widget
            node.addDOMWidget("vue_container", "div", container, {
                serialize: false,
            });

            // Set minimum node size
            node.size = [350, 450];
            node.setSize(node.size);

            // Load and mount Vue app
            const mount = await loadVueApp();
            if (mount) {
                // Find API endpoint from widgets
                const apiWidget = node.widgets?.find(w => w.name === "api_endpoint");
                const apiEndpoint = apiWidget ? apiWidget.value : "http://127.0.0.1:8189";

                mount(container, node, apiEndpoint);
                console.log("Prompt Skills: Vue app mounted for node", node.id, "API:", apiEndpoint);
            } else {
                // Fallback message
                container.innerHTML = `
                    <div style="padding: 20px; text-align: center; color: #888;">
                        <p>Vue app not loaded.</p>
                        <p style="font-size: 11px;">
                            Run <code>cd web && npm install && npm run build</code>
                        </p>
                    </div>
                `;
            }
        };
    },

    async nodeCreated(node, app) {
        if (node.comfyClass !== "OpencodeContainerNode") return;

        // Hide the default widgets since Vue app handles everything
        if (node.widgets) {
            for (const widget of node.widgets) {
                if (widget.name === "session_id") {
                    widget.type = "hidden";
                }
            }
        }
    }
});
