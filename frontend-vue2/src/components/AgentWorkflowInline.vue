<template>
  <div class="agent-workflow-inline">
    <div class="workflow-header">
      <span class="workflow-icon">🤖</span>
      <span class="workflow-title">Agent工作流程</span>
      <span class="workflow-status">{{ completedCount }}/{{ steps.length }} 已完成</span>
    </div>

    <div class="workflow-steps-compact">
      <div
        v-for="(step, index) in steps"
        :key="step.id"
        class="step-compact"
        :class="{
          'step-pending': step.status === 'pending',
          'step-processing': step.status === 'processing',
          'step-completed': step.status === 'completed'
        }"
      >
        <!-- 步骤头部 - 紧凑版 -->
        <div class="step-header-compact" @click="toggleStep(step)">
          <div class="step-indicator">
            <span v-if="step.status === 'pending'" class="step-number">{{ index + 1 }}</span>
            <span v-else-if="step.status === 'processing'" class="step-spinner">⏳</span>
            <span v-else class="step-check">✅</span>
          </div>

          <div class="step-info">
            <div class="step-name-row">
              <span class="step-icon">{{ step.icon }}</span>
              <span class="step-name">{{ step.name }}</span>
            </div>

            <!-- 简要信息预览 -->
            <div v-if="step.status === 'completed' && !step.expanded" class="step-preview">
              {{ getStepPreview(step) }}
            </div>
          </div>

          <div class="step-actions">
            <span v-if="step.expandable && step.status === 'completed'"
                  class="expand-icon"
                  :class="{ 'expanded': step.expanded }">
              ▼
            </span>
          </div>
        </div>

        <!-- 步骤详情（可展开） - 紧凑版 -->
        <transition name="slide-fade">
          <div v-if="step.expanded && step.details" class="step-details-compact">
            <!-- Query分析详情 -->
            <div v-if="step.id === 'query-analysis' && step.details.keywords" class="details-section">
              <div class="keywords-compact">
                <span v-for="keyword in step.details.keywords.slice(0, 3)"
                      :key="keyword.word"
                      class="keyword-tag">
                  {{ keyword.word }} <em>{{ (keyword.weight * 100).toFixed(0) }}%</em>
                </span>
              </div>
              <div class="intent-compact">
                意图：<strong>{{ step.details.intent }}</strong>
              </div>
            </div>

            <!-- 查询构造详情 -->
            <div v-else-if="step.id === 'query-construction' && step.details.queries" class="details-section">
              <div class="queries-compact">
                <div v-for="(query, idx) in step.details.queries[0].expanded.slice(0, 3)"
                     :key="idx"
                     class="query-item-compact">
                  {{ idx + 1 }}. {{ query }}
                </div>
              </div>
            </div>

            <!-- 知识库检索详情 -->
            <div v-else-if="step.id === 'knowledge-retrieval' && step.details.results" class="details-section">
              <div v-for="result in step.details.results.slice(0, 2)"
                   :key="result.docTitle"
                   class="result-compact">
                <div class="result-title-compact">
                  📚 {{ result.docTitle }}
                  <span class="relevance-badge">{{ (result.relevance * 100).toFixed(0) }}%</span>
                </div>
                <div class="result-excerpt-compact">{{ truncate(result.excerpt, 80) }}</div>
              </div>
            </div>

            <!-- 网络检索详情 -->
            <div v-else-if="step.id === 'web-retrieval' && step.details.results" class="details-section">
              <div v-for="result in step.details.results"
                   :key="result.url"
                   class="result-compact">
                <div class="result-title-compact">
                  🌐 {{ result.title }}
                  <span class="relevance-badge">{{ (result.relevance * 100).toFixed(0) }}%</span>
                </div>
                <div class="result-excerpt-compact">{{ truncate(result.excerpt, 80) }}</div>
              </div>
            </div>

            <!-- 多路PK详情 -->
            <div v-else-if="step.id === 'multi-source-pk' && step.details.comparisons" class="details-section">
              <div v-for="(comparison, idx) in step.details.comparisons.slice(0, 2)"
                   :key="idx"
                   class="comparison-compact"
                   :class="{ 'has-conflict': comparison.conflict }">
                <div class="comparison-topic">
                  {{ comparison.topic }}
                  <span v-if="comparison.conflict" class="conflict-tag">⚠️</span>
                </div>
                <div class="comparison-conclusion">{{ comparison.conclusion }}</div>
              </div>
            </div>

            <!-- 回复生成详情 -->
            <div v-else-if="step.id === 'response-generation' && step.details.outline" class="details-section">
              <div v-for="(section, idx) in step.details.outline"
                   :key="idx"
                   class="outline-compact">
                {{ idx + 1 }}. {{ section.section }}
              </div>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AgentWorkflowInline',
  props: {
    steps: {
      type: Array,
      required: true,
      default: () => []
    }
  },
  computed: {
    completedCount() {
      return this.steps.filter(s => s.status === 'completed').length
    }
  },
  methods: {
    toggleStep(step) {
      if (step.expandable && step.status === 'completed') {
        this.$set(step, 'expanded', !step.expanded)
      }
    },

    getStepPreview(step) {
      if (!step.details) return ''

      switch (step.id) {
        case 'query-analysis':
          return step.details.keywords ?
            `关键词: ${step.details.keywords.map(k => k.word).slice(0, 3).join('、')}` : ''
        case 'query-construction':
          return `生成了 ${step.details.totalQueries || 5} 个查询`
        case 'knowledge-retrieval':
          return `找到 ${step.details.totalResults || 0} 个相关文档`
        case 'web-retrieval':
          return `找到 ${step.details.totalResults || 0} 个网络资源`
        case 'multi-source-pk':
          return `对比了 ${step.details.comparisons?.length || 0} 个维度`
        case 'response-generation':
          return `生成 ${step.details.outline?.length || 0} 部分内容`
        default:
          return ''
      }
    },

    truncate(text, length) {
      if (!text) return ''
      return text.length > length ? text.substring(0, length) + '...' : text
    }
  }
}
</script>

<style scoped>
.agent-workflow-inline {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 12px;
  margin: 8px 0;
  border: 1px solid #e9ecef;
}

.workflow-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e9ecef;
}

.workflow-icon {
  font-size: 16px;
}

.workflow-title {
  font-weight: 600;
  font-size: 14px;
  color: #2c3e50;
  flex: 1;
}

.workflow-status {
  font-size: 12px;
  color: #868e96;
  background: #e9ecef;
  padding: 2px 8px;
  border-radius: 10px;
}

.workflow-steps-compact {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.step-compact {
  background: white;
  border-radius: 6px;
  overflow: hidden;
  transition: all 0.2s;
  border: 1px solid #e9ecef;
}

.step-pending {
  opacity: 0.6;
}

.step-processing {
  border-color: #74c0fc;
  box-shadow: 0 0 0 2px rgba(116, 192, 252, 0.1);
}

.step-completed {
  border-color: #e9ecef;
}

.step-header-compact {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.step-header-compact:hover {
  background: #f8f9fa;
}

.step-indicator {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.step-number {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #e9ecef;
  color: #868e96;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.step-spinner {
  font-size: 16px;
  animation: spin 2s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.step-check {
  font-size: 16px;
}

.step-info {
  flex: 1;
  min-width: 0;
}

.step-name-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 2px;
}

.step-icon {
  font-size: 14px;
}

.step-name {
  font-weight: 500;
  font-size: 13px;
  color: #495057;
}

.step-preview {
  font-size: 11px;
  color: #868e96;
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.step-actions {
  flex-shrink: 0;
  width: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.expand-icon {
  font-size: 10px;
  color: #868e96;
  transition: transform 0.2s;
}

.expand-icon.expanded {
  transform: rotate(180deg);
}

.step-details-compact {
  padding: 0 12px 12px 46px;
  font-size: 12px;
}

.details-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

/* Keywords */
.keywords-compact {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.keyword-tag {
  padding: 3px 8px;
  background: #e7f5ff;
  color: #1971c2;
  border-radius: 10px;
  font-size: 11px;
}

.keyword-tag em {
  font-style: normal;
  font-weight: 600;
  color: #f76707;
  margin-left: 4px;
}

.intent-compact {
  color: #495057;
  font-size: 11px;
}

.intent-compact strong {
  color: #1971c2;
}

/* Queries */
.queries-compact {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.query-item-compact {
  color: #495057;
  line-height: 1.4;
  padding-left: 4px;
}

/* Results */
.result-compact {
  padding: 6px 8px;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 2px solid #74c0fc;
}

.result-title-compact {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  font-weight: 500;
  color: #495057;
  margin-bottom: 3px;
  font-size: 11px;
}

.relevance-badge {
  padding: 1px 5px;
  background: #51cf66;
  color: white;
  border-radius: 8px;
  font-size: 10px;
  font-weight: 600;
  flex-shrink: 0;
}

.result-excerpt-compact {
  color: #6c757d;
  line-height: 1.4;
  font-size: 11px;
}

/* Comparisons */
.comparison-compact {
  padding: 6px 8px;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 2px solid #51cf66;
}

.comparison-compact.has-conflict {
  border-left-color: #ff8787;
  background: #fff5f5;
}

.comparison-topic {
  font-weight: 500;
  color: #495057;
  margin-bottom: 3px;
  font-size: 11px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.conflict-tag {
  font-size: 10px;
}

.comparison-conclusion {
  color: #6c757d;
  line-height: 1.4;
  font-size: 11px;
}

/* Outline */
.outline-compact {
  color: #495057;
  line-height: 1.4;
  padding-left: 4px;
}

/* Animation */
.slide-fade-enter-active {
  transition: all 0.3s ease;
}

.slide-fade-leave-active {
  transition: all 0.2s ease;
}

.slide-fade-enter,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}
</style>
