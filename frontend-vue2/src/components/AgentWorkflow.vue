<template>
  <div class="agent-workflow">
    <div class="workflow-title">
      <span class="title-icon">🤖</span>
      <span class="title-text">Agent工作流程</span>
    </div>

    <div class="workflow-steps">
      <div
        v-for="(step, index) in steps"
        :key="step.id"
        class="workflow-step"
        :class="{
          'step-pending': step.status === 'pending',
          'step-processing': step.status === 'processing',
          'step-completed': step.status === 'completed'
        }"
      >
        <!-- 步骤头部 -->
        <div class="step-header" @click="toggleStep(step)">
          <div class="step-header-left">
            <span class="step-icon">{{ step.icon }}</span>
            <span class="step-name">{{ step.name }}</span>
          </div>
          <div class="step-header-right">
            <span v-if="step.status === 'processing'" class="step-spinner">⏳</span>
            <span v-else-if="step.status === 'completed'" class="step-check">✅</span>
            <span v-if="step.expandable && step.status === 'completed'"
                  class="step-expand-icon"
                  :class="{ 'expanded': step.expanded }">
              ▼
            </span>
          </div>
        </div>

        <!-- 步骤详情（可展开） -->
        <transition name="slide-fade">
          <div v-if="step.expanded && step.details" class="step-details">
            <div class="details-title">{{ step.details.title }}</div>

            <!-- Query分析详情 -->
            <div v-if="step.id === 'query-analysis' && step.details.keywords" class="details-content">
              <div class="keywords-grid">
                <div v-for="keyword in step.details.keywords" :key="keyword.word" class="keyword-item">
                  <span class="keyword-word">{{ keyword.word }}</span>
                  <span class="keyword-meta">
                    <span class="keyword-weight">{{ (keyword.weight * 100).toFixed(0) }}%</span>
                    <span class="keyword-category">{{ keyword.category }}</span>
                  </span>
                </div>
              </div>
              <div class="intent-info">
                <span class="intent-label">识别意图：</span>
                <span class="intent-value">{{ step.details.intent }}</span>
                <span class="confidence-badge">置信度 {{ (step.details.confidence * 100).toFixed(0) }}%</span>
              </div>
            </div>

            <!-- 查询构造详情 -->
            <div v-else-if="step.id === 'query-construction' && step.details.queries" class="details-content">
              <div class="original-query">
                <div class="query-label">原始查询：</div>
                <div class="query-text">{{ step.details.queries[0].original }}</div>
              </div>
              <div class="expanded-queries">
                <div class="query-label">泛化查询（{{ step.details.queries[0].expanded.length }}条）：</div>
                <div class="query-list">
                  <div v-for="(query, idx) in step.details.queries[0].expanded"
                       :key="idx"
                       class="expanded-query-item">
                    <span class="query-index">{{ idx + 1 }}.</span>
                    <span class="query-content">{{ query }}</span>
                  </div>
                </div>
              </div>
              <div class="strategy-info">
                <span class="strategy-label">策略：</span>
                <span class="strategy-value">{{ step.details.queryStrategy }}</span>
              </div>
            </div>

            <!-- 知识库检索详情 -->
            <div v-else-if="step.id === 'knowledge-retrieval' && step.details.results" class="details-content">
              <div class="retrieval-summary">
                找到 <strong>{{ step.details.totalResults }}</strong> 条相关结果，
                平均相关度 <strong>{{ (step.details.avgRelevance * 100).toFixed(0) }}%</strong>
              </div>
              <div class="result-list">
                <div v-for="result in step.details.results" :key="result.docTitle" class="result-item">
                  <div class="result-header">
                    <span class="result-title">{{ result.docTitle }}</span>
                    <span class="result-relevance">{{ (result.relevance * 100).toFixed(0) }}%</span>
                  </div>
                  <div class="result-source">📚 {{ result.source }}</div>
                  <div class="result-excerpt">{{ result.excerpt }}</div>
                  <div class="result-keywords">
                    <span v-for="keyword in result.matchedKeywords"
                          :key="keyword"
                          class="matched-keyword">
                      #{{ keyword }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 网络检索详情 -->
            <div v-else-if="step.id === 'web-retrieval' && step.details.results" class="details-content">
              <div class="retrieval-summary">
                找到 <strong>{{ step.details.totalResults }}</strong> 条网络资源，
                平均相关度 <strong>{{ (step.details.avgRelevance * 100).toFixed(0) }}%</strong>
              </div>
              <div class="result-list">
                <div v-for="result in step.details.results" :key="result.url" class="result-item">
                  <div class="result-header">
                    <span class="result-title">{{ result.title }}</span>
                    <span class="result-relevance">{{ (result.relevance * 100).toFixed(0) }}%</span>
                  </div>
                  <div class="result-source">🌐 {{ result.source }}</div>
                  <div class="result-excerpt">{{ result.excerpt }}</div>
                  <div class="result-url">🔗 {{ result.url }}</div>
                </div>
              </div>
            </div>

            <!-- 多路PK详情 -->
            <div v-else-if="step.id === 'multi-source-pk' && step.details.comparisons" class="details-content">
              <div class="pk-summary">
                对比分析 <strong>{{ step.details.comparisons.length }}</strong> 个维度，
                一致率 <strong>{{ (step.details.agreementRate * 100).toFixed(0) }}%</strong>
                <span v-if="step.details.conflictCount > 0" class="conflict-count">
                  （{{ step.details.conflictCount }}个冲突）
                </span>
              </div>
              <div class="comparison-list">
                <div v-for="(comparison, idx) in step.details.comparisons"
                     :key="idx"
                     class="comparison-item"
                     :class="{ 'has-conflict': comparison.conflict }">
                  <div class="comparison-topic">
                    {{ comparison.topic }}
                    <span v-if="comparison.conflict" class="conflict-badge">⚠️ 存在冲突</span>
                  </div>
                  <div class="comparison-sources">
                    <div class="source-item knowledge-base">
                      <div class="source-label">📚 知识库：</div>
                      <div class="source-content">{{ comparison.knowledgeBase }}</div>
                    </div>
                    <div class="source-item web-source">
                      <div class="source-label">🌐 网络：</div>
                      <div class="source-content">{{ comparison.webSource }}</div>
                    </div>
                  </div>
                  <div class="comparison-conclusion">
                    <div class="conclusion-label">✅ 结论：</div>
                    <div class="conclusion-content">{{ comparison.conclusion }}</div>
                    <span class="confidence-badge">置信度 {{ (comparison.confidence * 100).toFixed(0) }}%</span>
                  </div>
                </div>
              </div>
              <div class="final-decision">
                <strong>最终决策：</strong>{{ step.details.finalDecision }}
              </div>
            </div>

            <!-- 回复生成详情 -->
            <div v-else-if="step.id === 'response-generation' && step.details.outline" class="details-content">
              <div class="generation-meta">
                <span>预计长度：{{ step.details.estimatedLength }}</span>
                <span class="separator">|</span>
                <span>风格：{{ step.details.tone }}</span>
              </div>
              <div class="outline-list">
                <div v-for="(section, idx) in step.details.outline"
                     :key="idx"
                     class="outline-item">
                  <div class="outline-section">{{ idx + 1 }}. {{ section.section }}</div>
                  <div class="outline-content">{{ section.content }}</div>
                </div>
              </div>
            </div>
          </div>
        </transition>

        <!-- 连接线 -->
        <div v-if="index < steps.length - 1" class="step-connector"></div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AgentWorkflow',
  props: {
    steps: {
      type: Array,
      required: true,
      default: () => []
    }
  },
  methods: {
    toggleStep(step) {
      if (step.expandable && step.status === 'completed') {
        this.$set(step, 'expanded', !step.expanded);
      }
    }
  }
};
</script>

<style scoped>
.agent-workflow {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  height: 100%;
  overflow-y: auto;
}

.workflow-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e9ecef;
}

.title-icon {
  font-size: 20px;
}

.workflow-steps {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.workflow-step {
  position: relative;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #e9ecef;
}

.step-header:hover {
  background: #f1f3f5;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.step-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.step-icon {
  font-size: 18px;
}

.step-name {
  font-weight: 500;
  color: #495057;
}

.step-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
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

.step-expand-icon {
  font-size: 12px;
  color: #868e96;
  transition: transform 0.2s;
}

.step-expand-icon.expanded {
  transform: rotate(180deg);
}

.step-pending {
  opacity: 0.5;
}

.step-processing .step-header {
  background: #e7f5ff;
  border-color: #74c0fc;
}

.step-completed .step-header {
  background: white;
}

.step-details {
  margin-top: 8px;
  padding: 12px;
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 6px;
}

.details-title {
  font-weight: 600;
  color: #495057;
  margin-bottom: 12px;
  font-size: 14px;
}

.details-content {
  font-size: 13px;
  color: #6c757d;
}

/* Query分析样式 */
.keywords-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}

.keyword-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #74c0fc;
}

.keyword-word {
  font-weight: 600;
  color: #1971c2;
}

.keyword-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
}

.keyword-weight {
  color: #f76707;
  font-weight: 600;
}

.keyword-category {
  color: #868e96;
  background: #e9ecef;
  padding: 2px 6px;
  border-radius: 3px;
}

.intent-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: #e7f5ff;
  border-radius: 4px;
}

.intent-label {
  font-weight: 600;
  color: #495057;
}

.intent-value {
  color: #1971c2;
  font-weight: 600;
}

.confidence-badge {
  margin-left: auto;
  padding: 2px 8px;
  background: #51cf66;
  color: white;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
}

/* 查询构造样式 */
.original-query,
.expanded-queries {
  margin-bottom: 12px;
}

.query-label {
  font-weight: 600;
  color: #495057;
  margin-bottom: 6px;
}

.query-text {
  padding: 8px;
  background: #e7f5ff;
  border-radius: 4px;
  color: #1971c2;
  font-weight: 500;
}

.query-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.expanded-query-item {
  display: flex;
  gap: 8px;
  padding: 6px 8px;
  background: #f8f9fa;
  border-radius: 4px;
}

.query-index {
  color: #868e96;
  font-weight: 600;
  min-width: 20px;
}

.query-content {
  color: #495057;
}

.strategy-info {
  padding: 8px;
  background: #fff3bf;
  border-radius: 4px;
}

.strategy-label {
  font-weight: 600;
  color: #495057;
}

.strategy-value {
  color: #f76707;
  font-weight: 500;
}

/* 检索结果样式 */
.retrieval-summary {
  padding: 8px;
  background: #e7f5ff;
  border-radius: 4px;
  margin-bottom: 12px;
  color: #495057;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-item {
  padding: 10px;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #74c0fc;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.result-title {
  font-weight: 600;
  color: #1971c2;
  flex: 1;
}

.result-relevance {
  padding: 2px 8px;
  background: #51cf66;
  color: white;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
}

.result-source {
  font-size: 12px;
  color: #868e96;
  margin-bottom: 6px;
}

.result-excerpt {
  color: #495057;
  line-height: 1.5;
  margin-bottom: 8px;
}

.result-url {
  font-size: 11px;
  color: #1971c2;
  word-break: break-all;
}

.result-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.matched-keyword {
  padding: 2px 6px;
  background: #e7f5ff;
  color: #1971c2;
  border-radius: 3px;
  font-size: 11px;
}

/* 多路PK样式 */
.pk-summary {
  padding: 8px;
  background: #fff3bf;
  border-radius: 4px;
  margin-bottom: 12px;
  color: #495057;
}

.conflict-count {
  color: #f03e3e;
  font-weight: 600;
}

.comparison-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 12px;
}

.comparison-item {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #51cf66;
}

.comparison-item.has-conflict {
  border-left-color: #ff8787;
  background: #fff5f5;
}

.comparison-topic {
  font-weight: 600;
  color: #495057;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.conflict-badge {
  padding: 2px 6px;
  background: #ff8787;
  color: white;
  border-radius: 3px;
  font-size: 11px;
}

.comparison-sources {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 8px;
}

.source-item {
  padding: 8px;
  border-radius: 4px;
}

.source-item.knowledge-base {
  background: #e7f5ff;
}

.source-item.web-source {
  background: #e3fafc;
}

.source-label {
  font-weight: 600;
  color: #495057;
  margin-bottom: 4px;
  font-size: 12px;
}

.source-content {
  color: #495057;
  line-height: 1.5;
}

.comparison-conclusion {
  padding: 8px;
  background: white;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.conclusion-label {
  font-weight: 600;
  color: #495057;
  font-size: 12px;
}

.conclusion-content {
  color: #495057;
  line-height: 1.5;
}

.final-decision {
  padding: 10px;
  background: #d0ebff;
  border-radius: 4px;
  color: #1971c2;
  line-height: 1.5;
}

/* 回复生成样式 */
.generation-meta {
  padding: 8px;
  background: #e7f5ff;
  border-radius: 4px;
  margin-bottom: 12px;
  color: #495057;
  display: flex;
  gap: 8px;
}

.separator {
  color: #dee2e6;
}

.outline-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.outline-item {
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
  border-left: 3px solid #74c0fc;
}

.outline-section {
  font-weight: 600;
  color: #1971c2;
  margin-bottom: 4px;
}

.outline-content {
  color: #495057;
  line-height: 1.5;
}

/* 连接线 */
.step-connector {
  width: 2px;
  height: 12px;
  background: #dee2e6;
  margin: 0 auto;
  margin-left: 28px;
}

/* 动画 */
.slide-fade-enter-active {
  transition: all 0.3s ease;
}

.slide-fade-leave-active {
  transition: all 0.2s ease;
}

.slide-fade-enter,
.slide-fade-leave-to {
  transform: translateY(-10px);
  opacity: 0;
}

/* 滚动条样式 */
.agent-workflow::-webkit-scrollbar {
  width: 6px;
}

.agent-workflow::-webkit-scrollbar-track {
  background: #f1f3f5;
  border-radius: 3px;
}

.agent-workflow::-webkit-scrollbar-thumb {
  background: #ced4da;
  border-radius: 3px;
}

.agent-workflow::-webkit-scrollbar-thumb:hover {
  background: #adb5bd;
}
</style>
