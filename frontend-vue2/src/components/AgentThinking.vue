<template>
  <div class="agent-thinking">
    <div class="header">
      <h3>
        <BrainCircuit class="header-icon" :size="20" :stroke-width="2" />
        <span>AI 代理思维过程</span>
      </h3>
      <p v-if="!isActive || steps.length === 0" class="subtitle">
        AI 代理将在这里展示分析和推理过程
      </p>
    </div>

    <div v-if="steps.length > 0" class="steps-list">
      <div class="timeline-track">
        <div
          v-for="step in steps"
          :key="step.id"
          class="timeline-step"
        >
          <div class="step-icon-shell">
            <component
              :is="getStepIconComponent(step)"
              class="step-icon"
              :size="14"
              :stroke-width="2"
            />
          </div>
          <div class="step-body">
            <div class="step-title">
              <span class="step-label">{{ getStepLabel(step) }}</span>
              <span class="step-time">{{ formatTime(step.timestamp) }}</span>
            </div>
            <div class="step-content">
              {{ step.content }}
            </div>
          </div>
        </div>
      </div>

      <div v-if="showCompletionBadge" class="completion-badge">
        回复生成完成
      </div>
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
import { BrainCircuit, Search, Shield, Target, Sparkles } from 'lucide-vue'

export default {
  name: 'AgentThinking',
  components: {
    BrainCircuit,
    Search,
    Shield,
    Target,
    Sparkles
  },
  data() {
    return {
      activeNames: []
    }
  },
  computed: {
    ...mapState('agent', ['steps', 'isActive']),
    showCompletionBadge() {
      return this.steps.length > 0 && !this.isActive
    }
  },
  methods: {
    getStepIconComponent(step) {
      const title = step.title || ''
      if (title.includes('开始新问题')) return 'Search'

      const icons = {
        thinking: 'Search',
        privacy: 'Shield',
        intent: 'Target',
        planning: 'Search',
        searching: 'Search',
        web: 'Search',
        parsing: 'Search',
        resolving: 'Target',
        generating: 'Sparkles'
      }
      return icons[step.type] || 'Search'
    },
    getStepLabel(step) {
      if (step.title) return step.title
      const type = step.type
      const labels = {
        thinking: '任务处理',
        privacy: '信息脱敏',
        intent: '意图识别',
        planning: '查询拆解',
        searching: '知识库检索',
        web: '网络检索',
        parsing: '读取文档',
        resolving: '冲突裁决',
        generating: '回复生成'
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
  background: rgba(253, 251, 249, 0.72);
  border: 1px solid #E8D5C4;
  border-radius: 12px;
}

.header {
  margin-bottom: 18px;
}

.header h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 700;
  color: #3C2F2F;
  margin: 0 0 8px 0;
}

.header-icon {
  color: #6B4423;
}

.subtitle {
  font-size: 13px;
  color: #8B7E74;
  margin: 0;
}

.steps-list {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}

.timeline-track {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 2px 0 10px 0;
}

.timeline-track::before {
  content: '';
  position: absolute;
  left: 15px;
  top: 14px;
  bottom: 14px;
  border-left: 1px dashed #D9BFA8;
}

.timeline-step {
  position: relative;
  display: grid;
  grid-template-columns: 32px minmax(0, 1fr);
  gap: 10px;
  padding: 8px 10px 8px 0;
  border-radius: 12px;
  transition: transform 0.3s ease, background 0.3s ease;
}

.timeline-step:hover {
  transform: translateX(4px);
  background: linear-gradient(90deg, rgba(244, 223, 190, 0.38), rgba(253, 251, 249, 0.04));
}

.step-icon-shell {
  position: relative;
  z-index: 1;
  width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #FBF4EA;
  border: 1px solid rgba(107, 68, 35, 0.1);
}

.step-icon {
  color: #6B4423;
}

.step-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  width: 100%;
}

.step-label {
  flex: 1;
  min-width: 0;
  font-size: 14px;
  font-weight: 600;
  color: #3F3A36;
}

.step-time {
  flex: 0 0 auto;
  font-size: 11px;
  color: #C2B7AE;
  font-family: 'Times New Roman', 'PingFang SC', 'Microsoft YaHei', serif;
}

.step-content {
  margin-top: 5px;
  font-size: 13px;
  color: #5F5750;
  line-height: 1.6;
}

.completion-badge {
  display: inline-flex;
  align-items: center;
  align-self: flex-start;
  margin-top: 8px;
  padding: 6px 12px;
  border-radius: 999px;
  background: #F0F9EB;
  border: 1px solid #DDEFD5;
  color: #4F7A45;
  font-size: 12px;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(79, 122, 69, 0.08);
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
