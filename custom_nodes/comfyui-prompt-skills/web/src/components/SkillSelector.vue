<template>
  <div class="skill-selector">
    <label>技能选择:</label>
    <div class="skills-list">
      <label 
        v-for="skill in skills" 
        :key="skill.id"
        class="skill-item"
        :class="{ selected: isSelected(skill.id) }"
      >
        <input
          type="checkbox"
          :checked="isSelected(skill.id)"
          @change="toggleSkill(skill.id)"
        />
        <span class="skill-name">{{ skill.name_zh || skill.name }}</span>
      </label>
    </div>
    <div v-if="skills.length === 0" class="no-skills">
      暂无可用技能
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'

export default {
  name: 'SkillSelector',
  props: {
    skills: {
      type: Array,
      default: () => []
    },
    selected: {
      type: Array,
      default: () => []
    }
  },
  emits: ['update:selected'],
  setup(props, { emit }) {
    const isSelected = (skillId) => {
      return props.selected.includes(skillId)
    }
    
    const toggleSkill = (skillId) => {
      const newSelected = isSelected(skillId)
        ? props.selected.filter(id => id !== skillId)
        : [...props.selected, skillId]
      emit('update:selected', newSelected)
    }
    
    return {
      isSelected,
      toggleSkill
    }
  }
}
</script>

<style scoped>
.skill-selector {
  margin-bottom: 8px;
}

.skill-selector label {
  font-size: 11px;
  color: #888;
  display: block;
  margin-bottom: 4px;
}

.skills-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.skill-item {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: #333;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.skill-item:hover {
  background: #444;
}

.skill-item.selected {
  background: #2d5a5a;
  color: #61dafb;
}

.skill-item input {
  display: none;
}

.skill-name {
  font-size: 11px;
}

.no-skills {
  font-size: 11px;
  color: #666;
  font-style: italic;
}
</style>
