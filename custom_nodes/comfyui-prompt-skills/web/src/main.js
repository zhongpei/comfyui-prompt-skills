import { createApp } from 'vue'
import App from './App.vue'

/**
 * Mount Vue application to a container element.
 * This is called from the ComfyUI extension.
 */
export function mountApp(container, nodeRef, apiEndpoint) {
    const app = createApp(App, {
        nodeRef: nodeRef,
        apiEndpoint: apiEndpoint
    })
    app.mount(container)
    return app
}

// Export for module usage
export { App }
