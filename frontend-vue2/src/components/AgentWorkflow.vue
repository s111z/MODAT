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
  background: linear-gradient(135deg, #FFFDF7 0%, #FFF9E6 100%);
  border-radius: 8px;
  padding: 16px;
  height: 100%;
  overflow-y: auto;
  border: 2px solid #FDE2BE;
}

.workflow-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #E47728;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid #FDE2BE;
}

.title-icon {
  font-size: 20px;
  filter: drop-shadow(0 1px 2px rgba(228, 119, 40, 0.2));
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
  border: 1px solid #FFF9E6;
}

.step-header:hover {
  background: linear-gradient(90deg, #FFF9E6 0%, #FFFDF7 100%);
  box-shadow: 0 2px 8px rgba(246, 165, 90, 0.15);
}

.step-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.step-icon {
  font-size: 18px;
  filter: drop-shadow(0 1px 2px rgba(228, 119, 40, 0.2));
}

.step-name {
  font-weight: 500;
  color: #E47728;
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
  color: #F6A55A;
  transition: transform 0.2s;
}

.step-expand-icon.expanded {
  transform: rotate(180deg);
}

.step-pending {
  opacity: 0.5;
}

.step-processing .step-header {
  background: linear-gradient(135deg, #FFF9E6 0%, #FFFDF7 100%);
  border-color: #F6A55A;
}

.step-completed .step-header {
  background: white;
}

.step-details {
  margin-top: 8px;
  padding: 12px;
  background: white;
  border: 1px solid #FDE2BE;
  border-radius: 6px;
}

.details-title {
  font-weight: 600;
  color: #E47728;
  margin-bottom: 12px;
  font-size: 14px;
}

.details-content {
  font-size: 13px;
  color: #595959;
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
  background: #FFF9E6;
  border-radius: 4px;
  border-left: 3px solid #F6A55A;
}

.keyword-word {
  font-weight: 600;
  color: #E47728;
}

.keyword-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
}

.keyword-weight {
  color: #E47728;
  font-weight: 600;
}

.keyword-category {
  color: #8c8c8c;
  background: #FDE2BE;
  padding: 2px 6px;
  border-radius: 3px;
}

.intent-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: linear-gradient(135deg, #FFF9E6 0%, #FFFDF7 100%);
  border-radius: 4px;
  border: 1px solid #FDE2BE;
}

.intent-label {
  font-weight: 600;
  color: #262626;
}

.intent-value {
  color: #E47728;
  font-weight: 600;
}

.confidence-badge {
  margin-left: auto;
  padding: 2px 8px;
  background: #E47728;
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
  color: #262626;
  margin-bottom: 6px;
}

.query-text {
  padding: 8px;
  background: linear-gradient(135deg, #FFF9E6 0%, #FFFDF7 100%);
  border-radius: 4px;
  color: #E47728;
  font-weight: 500;
  border: 1px solid #FDE2BE;
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
  background: #FFF9E6;
  border-radius: 4px;
}

.query-index {
  color: #F6A55A;
  font-weight: 600;
  min-width: 20px;
}

.query-content {
  color: #595959;
}

.strategy-info {
  padding: 8px;
  background: #FFF9E6;
  border-radius: 4px;
  border: 1px solid #FDE2BE;
}

.strategy-label {
  font-weight: 600;
  color: #262626;
}

.strategy-value {
  color: #E47728;
  font-weight: 500;
}

/* 检索结果样式 */
.retrieval-summary {
  padding: 8px;
  background: linear-gradient(135deg, #FFF9E6 0%, #FFFDF7 100%);
  border-radius: 4px;
  margin-bottom: 12px;
  color: #595959;
  border: 1px solid #FDE2BE;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-item {
  padding: 10px;
  background: #FFFDF7;
  border-radius: 4px;
  border-left: 3px solid #F6A55A;
  border: 1px solid #FDE2BE;
  border-left: 3px solid #F6A55A;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.result-title {
  font-weight: 600;
  color: #E47728;
  flex: 1;
}

.result-relevance {
  padding: 2px 8px;
  background: #E47728;
  color: white;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
}

.result-source {
  font-size: 12px;
  color: #8c8c8c;
  margin-bottom: 6px;
}

.result-excerpt {
  color: #595959;
  line-height: 1.5;
  margin-bottom: 8px;
}

.result-url {
  font-size: 11px;
  color: #E47728;
  word-break: break-all;
}

.result-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.matched-keyword {
  padding: 2px 6px;
  background: #FFF9E6;
  color: #E47728;
  border-radius: 3px;
  font-size: 11px;
  border: 1px solid #FDE2BE;
}

/* 多路PK样式 */
.pk-summary {
  padding: 8px;
  background: #FFF9E6;
  border-radius: 4px;
  margin-bottom: 12px;
  color: #595959;
  border: 1px solid #FDE2BE;
}

.conflict-count {
  color: #f56c6c;
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
  background: #FFFDF7;
  border-radius: 4px;
  border-left: 3px solid #52c41a;
  border: 1px solid #FDE2BE;
  border-left: 3px solid #52c41a;
}

.comparison-item.has-conflict {
  border-left-color: #f56c6c;
  background: #fff5f5;
}

.comparison-topic {
  font-weight: 600;
  color: #262626;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.conflict-badge {
  padding: 2px 6px;
  background: #f56c6c;
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
  background: linear-gradient(135deg, #FFF9E6 0%, #FFFDF7 100%);
  border: 1px solid #FDE2BE;
}

.source-item.web-source {
  background: linear-gradient(135deg, #FFFDF7 0%, #FFF9E6 100%);
  border: 1px solid #FDE2BE;
}

.source-label {
  font-weight: 600;
  color: #E47728;
  margin-bottom: 4px;
  font-size: 12px;
}

.source-content {
  color: #595959;
  line-height: 1.5;
}

.comparison-conclusion {
  padding: 8px;
  background: white;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  border: 1px solid #FDE2BE;
}

.conclusion-label {
  font-weight: 600;
  color: #E47728;
  font-size: 12px;
}

.conclusion-content {
  color: #595959;
  line-height: 1.5;
}

.final-decision {
  padding: 10px;
  background: linear-gradient(135deg, #FFF9E6 0%, #FFFDF7 100%);
  border-radius: 4px;
  color: #E47728;
  line-height: 1.5;
  border: 1px solid #FDE2BE;
  font-weight: 500;
}

/* 回复生成样式 */
.generation-meta {
  padding: 8px;
  background: linear-gradient(135deg, #FFF9E6 0%, #FFFDF7 100%);
  border-radius: 4px;
  margin-bottom: 12px;
  color: #595959;
  display: flex;
  gap: 8px;
  border: 1px solid #FDE2BE;
}

.separator {
  color: #d4b895;
}

.outline-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.outline-item {
  padding: 8px;
  background: #FFF9E6;
  border-radius: 4px;
  border-left: 3px solid #F6A55A;
}

.outline-section {
  font-weight: 600;
  color: #E47728;
  margin-bottom: 4px;
}

.outline-content {
  color: #595959;
  line-height: 1.5;
}

/* 连接线 */
.step-connector {
  width: 2px;
  height: 12px;
  background: #FDE2BE;
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
  background: #FFF9E6;
  border-radius: 3px;
}

.agent-workflow::-webkit-scrollbar-thumb {
  background: #F6A55A;
  border-radius: 3px;
}

.agent-workflow::-webkit-scrollbar-thumb:hover {
  background: #E47728;
}
</style>
