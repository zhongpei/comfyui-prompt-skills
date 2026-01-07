<template>
  <div class="debug-panel">
    <button class="toggle" @click="$emit('toggle')">
      🔧 Debug {{ visible ? '▼' : '▶' }}
    </button>
    <div v-if="visible" class="logs">
      <div 
        v-for="(log, idx) in logs" 
        :key="idx"
        class="log-entry"
        :class="log.level.toLowerCase()"
      >
        <span class="level">[{{ log.level }}]</span>
        <span class="module">{{ log.module }}:</span>
        <span class="message">{{ log.message }}</span>
      </div>
      <div v-if="logs.length === 0" class="empty">
        No logs yet...
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DebugPanel',
  props: {
    logs: {
      type: Array,
      default: () => []
    },
    visible: {
      type: Boolean,
      default: false
    }
  },
  emits: ['toggle']
}
</script>

<style scoped>
.debug-panel {
  margin-top: 8px;
  border-top: 1px solid #333;
  padding-top: 8px;
}

.toggle {
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  font-size: 11px;
  padding: 4px 0;
}

.toggle:hover {
  color: #aaa;
}

.logs {
  max-height: 100px;
  overflow-y: auto;
  margin-top: 4px;
  padding: 4px;
  background: #1a1a1a;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 10px;
}

.log-entry {
  padding: 2px 4px;
  display: flex;
  gap: 4px;
}

.log-entry.info { color: #8ec07c; }
.log-entry.debug { color: #83a598; }
.log-entry.warn { color: #fabd2f; }
.log-entry.error { color: #fb4934; }

.level {
  font-weight: bold;
  flex-shrink: 0;
}

.module {
  color: #b8bb26;
  flex-shrink: 0;
}

.message {
  color: #d5c4a1;
}

.empty {
  color: #666;
  font-style: italic;
  padding: 8px;
}
</style>
