<template>
  <div class="prompt-skills-app">
    <div class="header">
      <h3>Prompt Skills</h3>
      <span class="status" :class="status">{{ status }}</span>
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
    
    // Generate session ID
    const generateSessionId = () => {
      return 'ses_' + Math.random().toString(36).substring(2, 14)
    }
    
    // Initialize socket connection
    const initSocket = () => {
      sessionId.value = generateSessionId()
      
      // Connect to Flask backend (port 8189 default)
      // Note: This hardcoding is a limitation of the current decoupled architecture.
      // Ideally this config should flow from the node.
      socket.value = io('http://127.0.0.1:8189', {
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
      
      // Request skills list
      socket.value.emit('list_skills', { session_id: sessionId.value })
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
      sendMessage,
      updateSkills,
      abortGeneration
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
</style>
