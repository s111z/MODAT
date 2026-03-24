<template>
  <div class="agent-thinking">
    <div class="header">
      <h3>🧠 AI 代理思维过程</h3>
      <p v-if="!isActive || steps.length === 0" class="subtitle">
        AI 代理将在这里展示分析和推理过程
      </p>
    </div>

    <div v-if="steps.length > 0" class="steps-list">
      <el-collapse v-model="activeNames" accordion>
        <el-collapse-item
          v-for="step in steps"
          :key="step.id"
          :name="step.id"
        >
          <template slot="title">
            <div class="step-title">
              <span class="step-icon">{{ getStepIcon(step.type) }}</span>
              <span class="step-label">{{ getStepLabel(step.type) }}</span>
              <span class="step-time">{{ formatTime(step.timestamp) }}</span>
            </div>
          </template>
          <div class="step-content">
            {{ step.content }}
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>

    <div v-else class="empty-state">
      <img src="@/assets/images/wait.svg" class="wait-icon" alt="waiting" />
      <p>等待用户输入...</p>
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import dayjs from 'dayjs'

export default {
  name: 'AgentThinking',
  data() {
    return {
      activeNames: []
    }
  },
  computed: {
    ...mapState('agent', ['steps', 'isActive'])
  },
  methods: {
    getStepIcon(type) {
      const icons = {
        thinking: '🤔',
        searching: '🔍',
        parsing: '📄',
        resolving: '🔀',
        generating: '✨'
      }
      return icons[type] || '•'
    },
    getStepLabel(type) {
      const labels = {
        thinking: '思考中',
        searching: '搜索中',
        parsing: '解析中',
        resolving: '分析中',
        generating: '生成中'
      }
      return labels[type] || '处理中'
    },
    formatTime(timestamp) {
      return dayjs(timestamp).format('HH:mm:ss')
    }
  },
  watch: {
    steps: {
      handler(newSteps) {
        // 自动展开最新的步骤
        if (newSteps.length > 0) {
          const lastStep = newSteps[newSteps.length - 1]
          this.activeNames = [lastStep.id]
        }
      },
      immediate: true
    }
  }
}
</script>

<style scoped>
.agent-thinking {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 20px;
  background: transition;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}

.header {
  margin-bottom: 20px;
}

.header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0 0 8px 0;
}

.subtitle {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.steps-list {
  flex: 1;
  overflow-y: auto;
}

.step-title {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
}

.step-icon {
  font-size: 20px;
}

.step-label {
  flex: 1;
  font-weight: 500;
  color: #374151;
}

.step-time {
  font-size: 12px;
  color: #9ca3af;
  font-family: 'Monaco', 'Courier New', monospace;
}

.step-content {
  padding: 12px 16px;
  font-size: 14px;
  color: #6b7280;
  line-height: 1.6;
  background: #f9fafb;
  border-radius: 4px;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
}

.empty-state i {
  font-size: 48px;
  margin-bottom: 12px;
}

.empty-state p {
  font-size: 14px;
}
</style>
