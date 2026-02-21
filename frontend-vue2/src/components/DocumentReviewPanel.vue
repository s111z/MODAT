<template>
  <div class="document-review-panel">
    <!-- 阶段标签 -->
    <div class="phase-tabs">
      <div
        v-for="(phase, index) in phases"
        :key="phase.name"
        :class="['phase-tab', {
          active: currentPhase === phase.name,
          completed: isPhaseCompleted(index)
        }]"
        @click="handleTabClick(phase.name)"
      >
        <span class="phase-icon">{{ phase.icon }}</span>
        <span class="phase-label">{{ phase.label }}</span>
      </div>
    </div>

    <!-- 阶段内容 -->
    <div class="phase-content">
      <!-- 阶段1: 文档预览 -->
      <div v-show="currentPhase === 'document'" class="document-phase">
        <div class="document-header">
          <h3>📄 文档内容</h3>
          <el-tag v-if="documentInfo.fileName" type="info">{{ documentInfo.fileName }}</el-tag>
        </div>

        <div class="document-content-wrapper">
          <div :class="['document-content', { 'scanning': isScanning }]">
            <pre>{{ documentContent }}</pre>

            <!-- 扫描线动画 -->
            <div v-if="isScanning" class="scan-line"></div>
          </div>
        </div>

        <div v-if="isScanning" class="scanning-status">
          <i class="el-icon-loading"></i>
          <span>正在扫描文档...</span>
        </div>
      </div>

      <!-- 阶段2: 工作流程 -->
      <div v-show="currentPhase === 'workflow'" class="workflow-phase">
        <div class="workflow-header">
          <h3>⚙️ 审核工作流程</h3>
          <el-progress
            :percentage="workflowProgress"
            :status="workflowProgress === 100 ? 'success' : ''"
            class="workflow-progress"
          ></el-progress>
        </div>

        <el-collapse v-model="activeSteps" class="workflow-steps">
          <el-collapse-item
            v-for="(step, index) in workflowSteps"
            :key="step.id"
            :name="step.id"
            :disabled="step.status === 'pending'"
          >
            <!-- 步骤标题 -->
            <template slot="title">
              <div class="step-title">
                <span class="step-icon">{{ step.icon }}</span>
                <span class="step-name">{{ step.name }}</span>
                <el-tag
                  :type="getStepTagType(step.status)"
                  size="mini"
                  class="step-status"
                >
                  {{ getStepStatusText(step.status) }}
                </el-tag>
                <i v-if="step.status === 'in_progress'" class="el-icon-loading step-loading"></i>
              </div>
            </template>

            <!-- 步骤内容 -->
            <div class="step-content">
              <!-- Schema提取 -->
              <div v-if="step.id === 'schema-extraction' && step.details" class="schema-fields">
                <el-table :data="step.details.fields" size="small" stripe>
                  <el-table-column prop="name" label="字段名称" width="180"></el-table-column>
                  <el-table-column prop="value" label="提取值"></el-table-column>
                  <el-table-column prop="confidence" label="置信度" width="100">
                    <template slot-scope="scope">
                      <el-progress
                        :percentage="Math.round(scope.row.confidence * 100)"
                        :show-text="false"
                        :stroke-width="6"
                      ></el-progress>
                      <span class="confidence-text">{{ (scope.row.confidence * 100).toFixed(0) }}%</span>
                    </template>
                  </el-table-column>
                </el-table>
              </div>

              <!-- 查询构造 -->
              <div v-else-if="step.id === 'query-construction' && step.details" class="query-list">
                <el-tag
                  v-for="(query, qIndex) in step.details.queries"
                  :key="qIndex"
                  type="info"
                  size="small"
                  class="query-tag"
                >
                  {{ query }}
                </el-tag>
              </div>

              <!-- 知识库检索 -->
              <div v-else-if="step.id === 'knowledge-retrieval' && step.details" class="retrieval-results">
                <div
                  v-for="(result, rIndex) in step.details.results"
                  :key="rIndex"
                  class="result-item"
                >
                  <div class="result-header">
                    <span class="result-title">{{ result.title }}</span>
                    <el-tag size="mini" type="success">{{ (result.relevance * 100).toFixed(0) }}%</el-tag>
                  </div>
                  <p class="result-excerpt">{{ result.excerpt }}</p>
                </div>
              </div>

              <!-- 网络检索 -->
              <div v-else-if="step.id === 'web-retrieval' && step.details" class="retrieval-results">
                <div
                  v-for="(result, rIndex) in step.details.results"
                  :key="rIndex"
                  class="result-item"
                >
                  <div class="result-header">
                    <span class="result-source">🌐 {{ result.source }}</span>
                    <el-tag size="mini" type="success">{{ (result.relevance * 100).toFixed(0) }}%</el-tag>
                  </div>
                  <p class="result-excerpt">{{ result.excerpt }}</p>
                </div>
              </div>

              <!-- 多路PK -->
              <div v-else-if="step.id === 'multi-source-pk' && step.details" class="pk-analysis">
                <div
                  v-for="(analysis, aIndex) in step.details.analysis"
                  :key="aIndex"
                  class="analysis-item"
                >
                  <h4>{{ analysis.topic }}</h4>
                  <div class="comparison">
                    <div class="source-info">
                      <el-tag size="small" type="primary">知识库</el-tag>
                      <p>{{ analysis.knowledgeBase }}</p>
                    </div>
                    <div class="vs-divider">VS</div>
                    <div class="source-info">
                      <el-tag size="small" type="warning">网络</el-tag>
                      <p>{{ analysis.webSource }}</p>
                    </div>
                  </div>
                  <div class="conclusion">
                    <el-tag type="success" size="small">结论</el-tag>
                    <p>{{ analysis.conclusion }}</p>
                    <el-progress
                      :percentage="Math.round(analysis.confidence * 100)"
                      :show-text="false"
                      :stroke-width="4"
                    ></el-progress>
                  </div>
                </div>
              </div>

              <!-- 报告生成 / 回复生成 -->
              <div v-else-if="(step.id === 'report-generation' || step.id === 'response-generation') && step.details" class="generation-info">
                <el-steps :active="step.progress || 0" finish-status="success" simple>
                  <el-step
                    v-for="(section, sIndex) in (step.details.sections || step.details.outline)"
                    :key="sIndex"
                    :title="section"
                  ></el-step>
                </el-steps>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>

      <!-- 阶段3: 审核报告 -->
      <div v-show="currentPhase === 'result'" class="result-phase">
        <div class="report-header">
          <h3>📊 审核报告</h3>
          <div class="score-badge">
            <el-progress
              type="circle"
              :percentage="finalReport.complianceScore"
              :width="80"
              :color="getScoreColor(finalReport.complianceScore)"
            ></el-progress>
            <span class="score-label">合规评分</span>
          </div>
        </div>

        <div class="report-summary">
          <el-alert
            :title="finalReport.summary"
            type="info"
            :closable="false"
          ></el-alert>
        </div>

        <div class="report-section">
          <h4>✅ 符合项</h4>
          <el-card
            v-for="(item, index) in finalReport.compliantItems"
            :key="'compliant-' + index"
            class="report-card compliant-card"
            shadow="hover"
          >
            <div class="card-title">{{ item.title }}</div>
            <p class="card-description">{{ item.description }}</p>
            <el-tag size="mini" type="info">{{ item.reference }}</el-tag>
          </el-card>
        </div>

        <div class="report-section">
          <h4>⚠️ 需改进项</h4>
          <el-card
            v-for="(issue, index) in finalReport.issues"
            :key="'issue-' + index"
            :class="['report-card', 'issue-card', 'severity-' + issue.severity]"
            shadow="hover"
          >
            <div class="card-header">
              <div class="card-title">{{ issue.title }}</div>
              <el-tag
                :type="getSeverityTagType(issue.severity)"
                size="small"
              >
                优先级 {{ issue.priority }}
              </el-tag>
            </div>
            <p class="card-location">📍 {{ issue.location }}</p>
            <p class="card-description">{{ issue.description }}</p>
            <div class="card-suggestion">
              <el-tag size="mini" type="warning">建议</el-tag>
              <p>{{ issue.suggestion }}</p>
            </div>
          </el-card>
        </div>

        <div class="report-section">
          <h4>💡 改进建议</h4>
          <ul class="recommendations-list">
            <li v-for="(rec, index) in finalReport.recommendations" :key="'rec-' + index">
              {{ rec }}
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DocumentReviewPanel',
  props: {
    reviewData: {
      type: Object,
      default: () => ({})
    }
  },
  data() {
    return {
      phases: [
        { name: 'document', label: '文档预览', icon: '📄' },
        { name: 'workflow', label: '工作流程', icon: '⚙️' },
        { name: 'result', label: '审核报告', icon: '📊' }
      ],
      currentPhase: 'document',
      completedPhases: [],
      isScanning: false,
      documentContent: '',
      documentInfo: {},
      workflowSteps: [],
      activeSteps: [],
      finalReport: {
        complianceScore: 0,
        summary: '',
        compliantItems: [],
        issues: [],
        recommendations: []
      }
    }
  },
  computed: {
    workflowProgress() {
      if (this.workflowSteps.length === 0) return 0
      const completedCount = this.workflowSteps.filter(s => s.status === 'done').length
      return Math.round((completedCount / this.workflowSteps.length) * 100)
    }
  },
  methods: {
    // 更新文档内容
    updateDocumentContent(content) {
      this.documentContent = content
    },

    // 开始扫描
    startScanning() {
      this.isScanning = true
    },

    // 停止扫描
    stopScanning() {
      this.isScanning = false
    },

    // 切换阶段
    switchPhase(phase) {
      this.currentPhase = phase
      if (!this.completedPhases.includes(phase)) {
        this.completedPhases.push(phase)
      }
    },

    // 初始化工作流程
    initWorkflow(steps) {
      this.workflowSteps = steps.map(step => ({
        ...step,
        status: step.status || 'pending'
      }))
    },

    // 更新工作流程步骤
    updateWorkflowStep(stepIndex, updates) {
      if (stepIndex >= 0 && stepIndex < this.workflowSteps.length) {
        this.workflowSteps[stepIndex] = {
          ...this.workflowSteps[stepIndex],
          ...updates
        }

        // 如果步骤变为 in_progress，自动展开
        if (updates.status === 'in_progress') {
          const stepId = this.workflowSteps[stepIndex].id
          if (!this.activeSteps.includes(stepId)) {
            this.activeSteps.push(stepId)
          }
        }
      }
    },

    // 更新最终报告
    updateFinalReport(report) {
      this.finalReport = report
    },

    // 判断阶段是否完成
    isPhaseCompleted(index) {
      return this.completedPhases.includes(this.phases[index].name)
    },

    // 处理标签点击
    handleTabClick(phaseName) {
      // 只允许切换到已完成的阶段
      if (this.completedPhases.includes(phaseName)) {
        this.currentPhase = phaseName
      }
    },

    // 获取步骤标签类型
    getStepTagType(status) {
      const types = {
        done: 'success',
        in_progress: 'warning',
        pending: 'info'
      }
      return types[status] || 'info'
    },

    // 获取步骤状态文本
    getStepStatusText(status) {
      const texts = {
        done: '已完成',
        in_progress: '执行中',
        pending: '待执行'
      }
      return texts[status] || '待执行'
    },

    // 获取评分颜色
    getScoreColor(score) {
      if (score >= 90) return '#67c23a'
      if (score >= 70) return '#e6a23c'
      return '#f56c6c'
    },

    // 获取严重程度标签类型
    getSeverityTagType(severity) {
      const types = {
        high: 'danger',
        medium: 'warning',
        low: 'info'
      }
      return types[severity] || 'info'
    }
  }
}
</script>

<style scoped>
.document-review-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
  overflow: hidden;
}

/* 阶段标签 */
.phase-tabs {
  display: flex;
  border-bottom: 2px solid #e4e7ed;
  padding: 0 20px;
  background: #f5f7fa;
}

.phase-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px 20px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  color: #909399;
}

.phase-tab:hover {
  color: #409eff;
  background: rgba(64, 158, 255, 0.1);
}

.phase-tab.active {
  color: #409eff;
  font-weight: 600;
}

.phase-tab.active::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 2px;
  background: #409eff;
}

.phase-tab.completed .phase-icon {
  color: #67c23a;
}

.phase-icon {
  font-size: 20px;
}

.phase-label {
  font-size: 14px;
}

/* 阶段内容 */
.phase-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

/* 文档阶段 */
.document-phase {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.document-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.document-header h3 {
  margin: 0;
  font-size: 16px;
}

.document-content-wrapper {
  flex: 1;
  overflow: hidden;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  position: relative;
}

.document-content {
  height: 100%;
  overflow-y: auto;
  padding: 16px;
  background: #fafafa;
  position: relative;
}

.document-content pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.8;
  white-space: pre-wrap;
  color: #303133;
}

/* 扫描动画 */
.document-content.scanning {
  position: relative;
  overflow: hidden;
}

.scan-line {
  position: absolute;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, #409eff, transparent);
  box-shadow: 0 0 10px #409eff;
  animation: scan 2s linear infinite;
}

@keyframes scan {
  0% {
    top: 0;
  }
  100% {
    top: 100%;
  }
}

.scanning-status {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 8px 12px;
  background: #ecf5ff;
  border-radius: 4px;
  color: #409eff;
  font-size: 14px;
}

/* 工作流程阶段 */
.workflow-phase {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.workflow-header {
  margin-bottom: 20px;
}

.workflow-header h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
}

.workflow-progress {
  margin-bottom: 8px;
}

.workflow-steps {
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
  font-size: 18px;
}

.step-name {
  flex: 1;
  font-weight: 500;
}

.step-status {
  margin-left: auto;
}

.step-loading {
  color: #409eff;
  font-size: 16px;
}

.step-content {
  padding: 16px;
  background: #f9fafc;
  border-radius: 4px;
  margin-top: 8px;
}

/* Schema 字段 */
.schema-fields {
  margin-top: 12px;
}

.confidence-text {
  margin-left: 8px;
  font-size: 12px;
  color: #606266;
}

/* 查询列表 */
.query-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.query-tag {
  padding: 8px 12px;
}

/* 检索结果 */
.retrieval-results {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-item {
  padding: 12px;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.result-title,
.result-source {
  font-weight: 500;
  font-size: 14px;
  color: #303133;
}

.result-excerpt {
  margin: 0;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

/* PK 分析 */
.pk-analysis {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.analysis-item h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #303133;
}

.comparison {
  display: flex;
  gap: 16px;
  align-items: center;
  margin-bottom: 12px;
}

.source-info {
  flex: 1;
  padding: 12px;
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

.source-info p {
  margin: 8px 0 0 0;
  font-size: 13px;
  line-height: 1.6;
}

.vs-divider {
  font-weight: 600;
  color: #909399;
}

.conclusion {
  padding: 12px;
  background: #f0f9ff;
  border: 1px solid #bfdbfe;
  border-radius: 4px;
}

.conclusion p {
  margin: 8px 0 4px 0;
  font-size: 13px;
  line-height: 1.6;
}

/* 生成信息 */
.generation-info {
  padding: 16px;
}

/* 审核报告阶段 */
.result-phase {
  height: 100%;
  overflow-y: auto;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 2px solid #e4e7ed;
}

.report-header h3 {
  margin: 0;
  font-size: 18px;
}

.score-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.score-label {
  font-size: 12px;
  color: #606266;
}

.report-summary {
  margin-bottom: 24px;
}

.report-section {
  margin-bottom: 24px;
}

.report-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #303133;
}

.report-card {
  margin-bottom: 12px;
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.card-title {
  font-weight: 500;
  font-size: 14px;
  color: #303133;
  margin-bottom: 8px;
}

.card-location {
  margin: 0 0 8px 0;
  font-size: 12px;
  color: #909399;
}

.card-description {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

.card-suggestion {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #e4e7ed;
}

.card-suggestion p {
  margin: 8px 0 0 0;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

.compliant-card {
  border-left: 3px solid #67c23a;
}

.issue-card {
  border-left: 3px solid #e6a23c;
}

.issue-card.severity-high {
  border-left-color: #f56c6c;
}

.issue-card.severity-low {
  border-left-color: #909399;
}

.recommendations-list {
  margin: 0;
  padding-left: 24px;
}

.recommendations-list li {
  margin-bottom: 8px;
  font-size: 14px;
  line-height: 1.6;
  color: #606266;
}
</style>
