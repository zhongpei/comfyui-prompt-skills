<template>
  <div class="prompt-skills-app">
    <div class="header">
      <h3>Prompt Skills</h3>
      <span class="status" :class="status">{{ status }}</span>
    </div>
    
    <!-- OpenCode Session Management -->
    <div class="session-section">
      <div class="session-controls">
        <select v-model="currentOpencodeSession" @change="selectSession" class="session-select">
          <option value="">-- Select Session --</option>
          <option v-for="s in opencodeSessions" :key="s.id" :value="s.id">
            {{ s.title || s.id }}
          </option>
        </select>
        <button @click="createNewSession" class="session-btn new" title="New Session">+</button>
        <button @click="refreshSessions" class="session-btn refresh" title="Refresh">↻</button>
      </div>
    </div>
    
    <SkillSelector
      :skills="availableSkills"
      :selected="selectedSkills"
      @update:selected="updateSkills"
    />
    
    <ChatPanel
      :messages="messages"
      :streaming="streamingText"
      @send="sendMessage"
      @abort="abortGeneration"
      :isWorking="status === 'working'"
    />
    
    <DebugPanel
      :logs="debugLogs"
      :visible="showDebug"
      @toggle="showDebug = !showDebug"
    />
    
    <div class="output-section" v-if="lastOutput">
      <div class="output-tabs">
        <button 
          v-for="tab in ['english', 'json', 'bilingual']"
          :key="tab"
          :class="{ active: activeTab === tab }"
          @click="activeTab = tab"
        >
          {{ tab }}
        </button>
      </div>
      <div class="output-content">
        <pre v-if="activeTab === 'english'">{{ lastOutput.prompt_english }}</pre>
        <pre v-if="activeTab === 'json'">{{ lastOutput.prompt_json }}</pre>
        <pre v-if="activeTab === 'bilingual'">{{ lastOutput.prompt_bilingual }}</pre>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { io } from 'socket.io-client'
import ChatPanel from './components/ChatPanel.vue'
import SkillSelector from './components/SkillSelector.vue'
import DebugPanel from './components/DebugPanel.vue'

export default {
  name: 'PromptSkillsApp',
  components: {
    ChatPanel,
    SkillSelector,
    DebugPanel
  },
  props: {
    nodeRef: {
      type: Object,
      default: null
    },
    apiEndpoint: {
      type: String,
      default: 'http://127.0.0.1:8189'
    }
  },
  setup(props) {
    // State
    const socket = ref(null)
    const sessionId = ref('')
    const status = ref('idle')
    const messages = ref([])
    const streamingText = ref('')
    const debugLogs = ref([])
    const showDebug = ref(false)
    const availableSkills = ref([])
    const selectedSkills = ref(['z-photo'])
    const lastOutput = ref(null)
    const activeTab = ref('english')
    // OpenCode session management
    const opencodeSessions = ref([])
    const currentOpencodeSession = ref('')
    
    // Generate session ID
    const generateSessionId = () => {
      return 'ses_' + Math.random().toString(36).substring(2, 14)
    }
    
    // Initialize socket connection
    const initSocket = () => {
      sessionId.value = generateSessionId()
      
      // CRITICAL: Sync session ID to ComfyUI widget so the node can read it
      if (props.nodeRef && props.nodeRef.widgets) {
        const sessionWidget = props.nodeRef.widgets.find(w => w.name === 'session_id')
        if (sessionWidget) {
          sessionWidget.value = sessionId.value
          console.log('Prompt Skills: Synced session_id to widget:', sessionId.value)
        }
      }
      
      // Determine API URL
      // Priority: 1. Widget value (if in ComfyUI), 2. Prop, 3. Default
      let url = props.apiEndpoint || 'http://127.0.0.1:8189'
      
      if (props.nodeRef && props.nodeRef.widgets) {
        const apiWidget = props.nodeRef.widgets.find(w => w.name === 'api_endpoint')
        if (apiWidget && apiWidget.value) {
          url = apiWidget.value
          // Add listener for widget changes if possible
          apiWidget.callback = (v) => {
             // Optional: Handle dynamic changes if we want to auto-reconnect
             // For now, just logging
             console.log('API Endpoint widget changed to:', v)
          }
        }
      }

      debugLogs.value.push({
        level: 'INFO',
        module: 'System',
        message: `Connecting to ${url}...`
      })
      
      socket.value = io(url, {
        query: { session_id: sessionId.value },
        transports: ['websocket'],
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000
      })
      
      // Handle connection
      socket.value.on('connect', () => {
        debugLogs.value.push({
          level: 'INFO',
          module: 'Socket',
          message: 'Connected to server'
        })
      })
      
      // Handle state sync
      socket.value.on('sync_state', (data) => {
        messages.value = data.history || []
        status.value = data.status || 'idle'
        if (data.skills) {
          selectedSkills.value = data.skills
        }
      })
      
      // Handle streaming
      socket.value.on('stream_delta', (data) => {
        streamingText.value += data.delta
      })
      
      // Handle debug logs
      socket.value.on('debug_log', (data) => {
        debugLogs.value.push(data)
        if (debugLogs.value.length > 100) {
          debugLogs.value.shift()
        }
      })
      
      // Handle status updates
      socket.value.on('status_update', (data) => {
        status.value = data.status
      })
      
      // Handle completion
      socket.value.on('complete', (data) => {
        lastOutput.value = data
        streamingText.value = ''
        messages.value.push({
          role: 'assistant',
          content: data.prompt_english
        })
        
        // Re-sync session ID to widget after completion to ensure ComfyUI has latest
        if (props.nodeRef && props.nodeRef.widgets) {
          const sessionWidget = props.nodeRef.widgets.find(w => w.name === 'session_id')
          if (sessionWidget) {
            sessionWidget.value = sessionId.value
            console.log('Prompt Skills: [complete] Re-synced session_id to widget:', sessionId.value)
          }
        }
      })
      
      // Handle errors
      socket.value.on('error', (data) => {
        debugLogs.value.push({
          level: 'ERROR',
          module: 'Server',
          message: data.message
        })
        status.value = 'error'
      })
      
      // Handle skills list
      socket.value.on('skills_list', (data) => {
        availableSkills.value = data.skills
      })
      
      // Handle OpenCode session events
      socket.value.on('opencode_sessions_list', (data) => {
        opencodeSessions.value = data.sessions || []
      })
      
      socket.value.on('opencode_session_changed', (data) => {
        currentOpencodeSession.value = data.opencode_session_id || ''
        debugLogs.value.push({
          level: 'INFO',
          module: 'Session',
          message: `Switched to OpenCode session: ${data.opencode_session_id || 'none'}`
        })
      })
      
      // Request skills list and sessions
      socket.value.emit('list_skills', { session_id: sessionId.value })
      socket.value.emit('list_opencode_sessions', { session_id: sessionId.value })
    }
    
    // Send message
    const sendMessage = (content) => {
      if (!content.trim() || !socket.value) return
      
      messages.value.push({
        role: 'user',
        content: content
      })
      streamingText.value = ''
      
      socket.value.emit('user_message', {
        session_id: sessionId.value,
        content: content,
        model_target: 'z-image-turbo'
      })
    }
    
    // Update skills
    const updateSkills = (skills) => {
      selectedSkills.value = skills
      if (socket.value) {
        socket.value.emit('configure', {
          session_id: sessionId.value,
          active_skills: skills
        })
      }
    }
    
    // Abort generation
    const abortGeneration = () => {
      if (socket.value) {
        socket.value.emit('abort', { session_id: sessionId.value })
      }
    }
    
    // OpenCode Session Management
    const createNewSession = () => {
      if (socket.value) {
        socket.value.emit('create_opencode_session', { 
          session_id: sessionId.value,
          title: `Session ${Date.now()}`
        })
        // Refresh the list after creating
        setTimeout(() => {
          socket.value.emit('list_opencode_sessions', { session_id: sessionId.value })
        }, 500)
      }
    }
    
    const selectSession = () => {
      if (socket.value && currentOpencodeSession.value) {
        socket.value.emit('select_opencode_session', {
          session_id: sessionId.value,
          opencode_session_id: currentOpencodeSession.value
        })
      }
    }
    
    const refreshSessions = () => {
      if (socket.value) {
        socket.value.emit('list_opencode_sessions', { session_id: sessionId.value })
      }
    }
    
    // Lifecycle
    onMounted(() => {
      initSocket()
    })
    
    onUnmounted(() => {
      if (socket.value) {
        socket.value.disconnect()
      }
    })
    
    return {
      status,
      messages,
      streamingText,
      debugLogs,
      showDebug,
      availableSkills,
      selectedSkills,
      lastOutput,
      activeTab,
      opencodeSessions,
      currentOpencodeSession,
      sendMessage,
      updateSkills,
      abortGeneration,
      createNewSession,
      selectSession,
      refreshSessions
    }
  }
}
</script>

<style scoped>
.prompt-skills-app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 12px;
  padding: 8px;
  background: #1e1e1e;
  color: #e0e0e0;
  border-radius: 4px;
  min-width: 300px;
  max-height: 400px;
  overflow-y: auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #333;
}

.header h3 {
  margin: 0;
  font-size: 14px;
  color: #61dafb;
}

.status {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 10px;
  text-transform: uppercase;
}

.status.idle { background: #2d5a2d; color: #98fb98; }
.status.working { background: #5a5a2d; color: #fbfb98; }
.status.error { background: #5a2d2d; color: #fb9898; }

.output-section {
  margin-top: 8px;
  border-top: 1px solid #333;
  padding-top: 8px;
}

.output-tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 8px;
}

.output-tabs button {
  padding: 4px 8px;
  border: none;
  background: #333;
  color: #888;
  border-radius: 4px;
  cursor: pointer;
  font-size: 10px;
  text-transform: capitalize;
}

.output-tabs button.active {
  background: #61dafb;
  color: #1e1e1e;
}

.output-content pre {
  background: #2d2d2d;
  padding: 8px;
  border-radius: 4px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 11px;
  margin: 0;
}

/* Session Management */
.session-section {
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #333;
}

.session-controls {
  display: flex;
  gap: 4px;
  align-items: center;
}

.session-select {
  flex: 1;
  padding: 4px 6px;
  border: 1px solid #444;
  background: #2d2d2d;
  color: #e0e0e0;
  border-radius: 4px;
  font-size: 11px;
}

.session-btn {
  padding: 4px 8px;
  border: none;
  background: #333;
  color: #888;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.session-btn:hover {
  background: #444;
  color: #e0e0e0;
}

.session-btn.new {
  background: #2d5a2d;
  color: #98fb98;
}

.session-btn.new:hover {
  background: #3d7a3d;
}
</style>
