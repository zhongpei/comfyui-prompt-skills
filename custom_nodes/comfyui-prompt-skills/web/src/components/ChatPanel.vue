<template>
  <div class="chat-panel">
    <div class="messages" ref="messagesContainer">
      <div 
        v-for="(msg, idx) in messages" 
        :key="idx" 
        class="message"
        :class="msg.role"
      >
        <span class="role">{{ msg.role === 'user' ? '👤' : '🤖' }}</span>
        <span class="content">{{ msg.content }}</span>
      </div>
      <div v-if="streaming" class="message assistant streaming">
        <span class="role">🤖</span>
        <span class="content">{{ streaming }}<span class="cursor">▌</span></span>
      </div>
    </div>
    
    <div class="input-area">
      <textarea
        v-model="input"
        placeholder="描述您想要生成的图像..."
        @keydown.enter.prevent="handleSend"
        :disabled="isWorking"
        rows="2"
      ></textarea>
      <div class="buttons">
        <button 
          v-if="isWorking" 
          @click="$emit('abort')"
          class="abort"
        >
          停止
        </button>
        <button 
          v-else
          @click="handleSend"
          :disabled="!input.trim()"
          class="send"
        >
          发送
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, nextTick } from 'vue'

export default {
  name: 'ChatPanel',
  props: {
    messages: {
      type: Array,
      default: () => []
    },
    streaming: {
      type: String,
      default: ''
    },
    isWorking: {
      type: Boolean,
      default: false
    }
  },
  emits: ['send', 'abort'],
  setup(props, { emit }) {
    const input = ref('')
    const messagesContainer = ref(null)
    
    const handleSend = () => {
      if (input.value.trim() && !props.isWorking) {
        emit('send', input.value)
        input.value = ''
      }
    }
    
    // Auto-scroll on new messages
    watch(
      () => [props.messages.length, props.streaming],
      () => {
        nextTick(() => {
          if (messagesContainer.value) {
            messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
          }
        })
      }
    )
    
    return {
      input,
      messagesContainer,
      handleSend
    }
  }
}
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.messages {
  max-height: 150px;
  overflow-y: auto;
  padding: 4px;
  background: #2d2d2d;
  border-radius: 4px;
}

.message {
  padding: 4px 8px;
  margin-bottom: 4px;
  border-radius: 4px;
  display: flex;
  gap: 8px;
}

.message.user {
  background: #1e3a5f;
}

.message.assistant {
  background: #2d3d2d;
}

.message .role {
  flex-shrink: 0;
}

.message .content {
  word-break: break-word;
}

.message.streaming .cursor {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.input-area {
  display: flex;
  gap: 4px;
}

.input-area textarea {
  flex: 1;
  padding: 8px;
  border: 1px solid #444;
  border-radius: 4px;
  background: #2d2d2d;
  color: #e0e0e0;
  font-size: 12px;
  resize: none;
}

.input-area textarea:focus {
  outline: none;
  border-color: #61dafb;
}

.input-area textarea:disabled {
  opacity: 0.5;
}

.buttons {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.buttons button {
  padding: 8px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
}

.buttons button.send {
  background: #61dafb;
  color: #1e1e1e;
}

.buttons button.send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.buttons button.abort {
  background: #fb6161;
  color: #fff;
}
</style>
