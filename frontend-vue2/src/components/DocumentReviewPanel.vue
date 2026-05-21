<template>
  <div class="document-review-panel">
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
        <component
          :is="phase.icon"
          class="phase-icon"
          :size="16"
          :stroke-width="2"
        />
        <span class="phase-label">{{ phase.label }}</span>
      </div>
    </div>

    <div class="phase-content">
      
      <div v-show="currentPhase === 'document'" class="document-phase">
        <div class="document-header">
          <h3>文档内容</h3>
          <el-tag v-if="documentInfo.fileName" type="info">{{ documentInfo.fileName }}</el-tag>
        </div>
        <div class="document-content-wrapper">
          <div :class="['document-content', { 'scanning': isScanning }]">
            <pre>{{ documentContent }}</pre>
            <div v-if="isScanning" class="scan-line"></div>
          </div>
        </div>
        <div class="review-upload-action">
          <el-button
            type="warning"
            icon="el-icon-document-add"
            class="review-upload-btn"
            :loading="isScanning"
            @click="$emit('request-review-upload')"
          >
            方案审核
          </el-button>
        </div>
        <div v-if="isScanning" class="scanning-status">
          <i class="el-icon-loading"></i>
          <span>正在扫描文档...</span>
        </div>
      </div>

      <div v-show="currentPhase === 'workflow'" class="workflow-phase">
        <div class="workflow-header-card">
          <div class="workflow-title-row">
            <i class="el-icon-setting title-icon"></i>
            <span class="title-text">审核工作流程</span>
          </div>
          <el-progress
            :percentage="workflowProgress"
            :show-text="true"
            :stroke-width="4"
            class="custom-progress"
            color="#409eff"
          ></el-progress>
        </div>

        <el-collapse v-model="activeSteps" class="flat-workflow-steps">
          <el-collapse-item
            v-for="(step, index) in workflowSteps"
            :key="step.id"
            :name="step.id"
            :disabled="step.status !== 'done' && step.status !== 'in_progress' && step.status !== 'processing'"
          >
            <template slot="title">
              <div class="step-title-bar">
                <div class="step-left">
                  <span class="step-icon">{{ step.icon }}</span>
                  <span class="step-name">{{ step.name }}</span>
                </div>
                <div class="step-right">
                  <el-badge
                    v-if="step.logs && step.logs.length"
                    :value="step.logs.length"
                    class="log-count-badge"
                    type="warning"
                  />
                  <span v-if="step.status === 'done'" class="status-text success">
                    已完成 <i class="el-icon-caret-bottom collapse-arrow"></i>
                  </span>
                  <span v-else-if="step.status === 'in_progress' || step.status === 'processing'" class="status-text processing">
                    <i class="el-icon-loading"></i> 执行中
                  </span>
                  <span v-else class="status-text pending">
                    待执行
                  </span>
                </div>
              </div>
            </template>

            <div class="step-detail-content">
              <div class="node-log-panel">
                <div class="node-log-header">
                  <div>
                    <i class="el-icon-tickets"></i>
                    <span>节点过程日志</span>
                  </div>
                  <span class="node-log-subtitle">同步后端命令行中的审核进度</span>
                </div>
                <div v-if="step.logs && step.logs.length" class="node-log-list">
                  <div
                    v-for="(log, logIndex) in step.logs"
                    :key="logIndex"
                    class="node-log-row"
                  >
                    <span class="node-log-time">{{ log.time }}</span>
                    <span class="node-log-message">{{ log.message }}</span>
                  </div>
                </div>
                <div v-else class="node-log-empty">等待该节点输出过程日志...</div>
              </div>
              
              <div v-if="step.id === 'schema-extraction' && step.details" class="schema-fields">
                <el-table :data="step.details.fields" size="small" stripe border>
                  <el-table-column prop="name" label="字段名称" width="160"></el-table-column>
                  <el-table-column prop="value" label="提取值"></el-table-column>
                  <el-table-column prop="confidence" label="置信度" width="100">
                    <template slot-scope="scope">
                      <span class="confidence-text">{{ (scope.row.confidence * 100).toFixed(0) }}%</span>
                    </template>
                  </el-table-column>
                </el-table>
              </div>

              <div v-else-if="step.id === 'query-construction' && step.details" class="query-list">
                <el-tag v-for="(query, qIndex) in step.details.queries" :key="qIndex" type="info" size="small" class="query-tag">
                  <i class="el-icon-search"></i> {{ query }}
                </el-tag>
              </div>

              <div v-else-if="step.id === 'mcp-routing' && step.details" class="mcp-servers-list">
                <div v-for="(server, sIndex) in step.details.servers" :key="sIndex"
                     :class="['mcp-server-container', {
                       'calc-server-highlight': server.id === 'calc-server',
                       'compliance-server-highlight': server.id === 'compliance-server'
                     }]">
                  <div class="mcp-server-row" @click="server.status === 'done' && toggleServer(sIndex)">
                    <div class="server-left">
                      <span class="server-icon">{{ server.icon }}</span>
                      <span class="server-name" :class="{'text-disabled': server.status !== 'done' && server.status !== 'in_progress'}">
                        {{ server.name }}
                        <el-tag v-if="server.id === 'calc-server'" size="mini" type="warning" effect="plain">数值校验</el-tag>
                        <el-tag v-if="server.id === 'compliance-server'" size="mini" type="danger" effect="plain">资质审查</el-tag>
                      </span>
                    </div>
                    <div class="server-right">
                      <span v-if="server.status === 'done'" class="status-text success" style="margin-right: 8px;">已完成</span>
                      <span v-else-if="server.status === 'in_progress' || server.status === 'processing'" class="status-text processing" style="margin-right: 8px;"><i class="el-icon-loading"></i> 执行中</span>
                      <span v-else class="status-text pending" style="margin-right: 8px;">待执行</span>
                      <i v-if="server.status === 'done'" :class="expandedServers.includes(sIndex) ? 'el-icon-arrow-down' : 'el-icon-arrow-right'" class="server-arrow"></i>
                    </div>
                  </div>
                  <div v-show="expandedServers.includes(sIndex)"
                       :class="['server-details-content', {
                         'calc-server-content': server.id === 'calc-server',
                         'compliance-server-content': server.id === 'compliance-server'
                       }]">
                    <!-- 计算校验 Server 特殊展示 -->
                    <div v-if="server.id === 'calc-server'" class="calc-server-results">
                      <div v-for="(res, rIndex) in server.results" :key="rIndex" class="calc-card">
                        <div class="calc-card-header">
                          <span class="calc-icon-warning">!</span>
                          <span class="calc-card-title">{{ res.title }}</span>
                        </div>

                        <div class="calc-section">
                          <div class="calc-label">系统警告:</div>
                          <div class="calc-box-warning">{{ res.excerpt }}</div>
                        </div>

                        <div v-if="res.calculation" class="calc-section calc-box-formula-wrapper">
                          <div class="calc-label">计算公式:</div>
                          <div class="calc-box-formula-inner">{{ res.calculation }}</div>
                        </div>

                        <div v-if="res.correction" class="calc-section calc-box-suggestion">
                          <div class="calc-suggestion-label">纠正建议</div>
                          <div class="calc-suggestion-content">{{ res.correction }}</div>
                        </div>
                      </div>
                    </div>

                    <!-- 合规审查 Server 特殊展示 -->
                    <div v-else-if="server.id === 'compliance-server'">
                      <div v-for="(res, rIndex) in server.results" :key="rIndex" class="compliance-result-item">
                        <div class="compliance-header">
                          <i class="el-icon-office-building"></i>
                          <div class="compliance-title-group">
                            <span class="compliance-title">{{ res.companyName }}</span>
                            <span class="compliance-subtitle">{{ res.title }}</span>
                          </div>
                          <el-tag v-if="res.status === 'qualified'" type="success" size="mini">
                            <i class="el-icon-circle-check"></i> 资质齐全
                          </el-tag>
                          <el-tag v-else-if="res.status === 'unqualified'" type="danger" size="mini">
                            <i class="el-icon-circle-close"></i> 资质缺失
                          </el-tag>
                          <el-tag v-else-if="res.status === 'warning'" type="warning" size="mini">
                            <i class="el-icon-warning"></i> 待核查
                          </el-tag>
                        </div>
                        <div class="compliance-content">
                          <div class="company-info-box">
                            <div class="info-label">
                              <i class="el-icon-search"></i> 检索来源
                            </div>
                            <div class="info-value">{{ res.source }}</div>
                          </div>
                          <div class="compliance-detail">{{ res.excerpt }}</div>
                          <div v-if="res.checkItems && res.checkItems.length" class="compliance-check-items">
                            <div class="check-items-label">资质核查项:</div>
                            <div class="check-items-list">
                              <div v-for="(item, itemIdx) in res.checkItems" :key="itemIdx" class="check-item-row">
                                <i v-if="item.passed" class="el-icon-circle-check check-icon-pass"></i>
                                <i v-else class="el-icon-circle-close check-icon-fail"></i>
                                <span class="check-item-name">{{ item.name }}</span>
                                <span class="check-item-result" :class="{'result-pass': item.passed, 'result-fail': !item.passed}">
                                  {{ item.result }}
                                </span>
                              </div>
                            </div>
                          </div>
                          <div v-if="res.riskLevel" class="risk-assessment">
                            <div class="risk-label">
                              <i class="el-icon-warning-outline"></i> 风险评估
                            </div>
                            <el-tag v-if="res.riskLevel === 'high'" type="danger" size="small">高风险</el-tag>
                            <el-tag v-else-if="res.riskLevel === 'medium'" type="warning" size="small">中风险</el-tag>
                            <el-tag v-else type="success" size="small">低风险</el-tag>
                            <span class="risk-desc">{{ res.riskDescription }}</span>
                          </div>
                          <div v-if="res.suggestion" class="compliance-suggestion">
                            <el-alert :title="res.suggestion" type="warning" :closable="false" show-icon></el-alert>
                          </div>
                        </div>
                      </div>
                    </div>

                    <!-- 其他普通 Server 展示 -->
                    <div v-else>
                      <div v-for="(res, rIndex) in server.results" :key="rIndex" class="res-item">
                        <div class="res-title">{{ res.title || res.source }}</div>
                        <div class="res-desc">{{ res.excerpt }}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div v-else-if="step.id === 'multi-channel-alignment' && step.details" class="alignment-box">
                <el-alert v-if="step.status === 'done'" :title="step.details.status || '解析对齐完成'" type="success" :closable="false" show-icon></el-alert>
                <el-alert v-else-if="step.status === 'in_progress' || step.status === 'processing'" title="正在进行多渠道数据对齐..." type="warning" :closable="false" show-icon></el-alert>
                <el-alert v-else title="待执行数据对齐..." type="info" :closable="false" show-icon></el-alert>
                
                <div class="channel-tags" style="margin-top: 8px;">
                  <el-tag v-for="(ch, cIndex) in step.details.channels" :key="cIndex" :type="step.status === 'done' ? 'primary' : 'info'" effect="plain" size="small">
                    {{ ch }}
                  </el-tag>
                </div>
              </div>

              <div v-else-if="step.id === 'multi-source-pk' && step.details" class="pk-analysis">
                <div v-for="(analysis, aIndex) in step.details.analysis" :key="aIndex" class="analysis-item">
                  <h4>{{ analysis.topic }}</h4>
                  <div class="comparison">
                    <div class="source-info">
                      <el-tag size="small" type="info">基础源</el-tag>
                      <p>{{ analysis.knowledgeBase }}</p>
                    </div>
                    <div class="vs-divider">VS</div>
                    <div class="source-info">
                      <el-tag size="small" type="warning">外部/校验</el-tag>
                      <p>{{ analysis.webSource }}</p>
                    </div>
                  </div>
                  <div class="conclusion">
                    <el-tag :type="step.status === 'done' ? 'success' : 'info'" size="small">对齐结论</el-tag>
                    <p v-if="step.status === 'done'">{{ analysis.conclusion }}</p>
                    <p v-else-if="step.status === 'in_progress' || step.status === 'processing'" class="text-pending-italic">分析判定中...</p>
                    <p v-else class="text-pending-italic">待执行...</p>
                  </div>
                </div>
              </div>

              <div v-else-if="step.id === 'quality-check' && step.details" class="quality-check-box">
                <div v-for="(check, cIndex) in step.details.checks" :key="cIndex" class="check-item">
                  <i v-if="step.status === 'done'" :class="check.passed ? 'el-icon-circle-check text-success' : 'el-icon-warning text-warning'"></i>
                  <i v-else-if="step.status === 'in_progress' || step.status === 'processing'" class="el-icon-loading text-processing"></i>
                  <i v-else class="el-icon-time text-pending"></i>
                  
                  <div class="check-content">
                    <div class="check-title">{{ check.item }}</div>
                    <div class="check-note" v-if="step.status === 'done'">{{ check.note }}</div>
                    <div class="check-note" v-else-if="step.status === 'in_progress' || step.status === 'processing'">正在进行风险自查逻辑推演...</div>
                    <div class="check-note" v-else>待执行自查...</div>
                  </div>
                </div>
              </div>

              <div v-else-if="step.id === 'plan-rewrite' && step.details" 
                   class="rewrite-box" 
                   :class="{'clickable-box': step.status === 'done'}" 
                   @click="step.status === 'done' && switchPhase('optimization')">
                <div class="rewrite-header">
                  <template v-if="step.status === 'done'">
                    <i class="el-icon-document-checked"></i>
                    <span>优化方案已生成，点击前往查阅 <i class="el-icon-right"></i></span>
                  </template>
                  <template v-else-if="step.status === 'in_progress' || step.status === 'processing'">
                    <i class="el-icon-loading" style="color: #409eff;"></i>
                    <span style="color: #409eff;">正在重写合规方案...</span>
                  </template>
                  <template v-else>
                    <i class="el-icon-document" style="color: #909399;"></i>
                    <span style="color: #909399;">待执行方案重写</span>
                  </template>
                </div>
              </div>

              <div v-else-if="(step.id === 'report-generation' || step.id === 'response-generation') && step.details" 
                   class="generation-info" 
                   :class="{'clickable-box': step.status === 'done'}" 
                   @click="step.status === 'done' && switchPhase('result')">
                <div class="generation-title">
                  <template v-if="step.status === 'done'">
                    <i class="el-icon-data-line"></i> 报告已生成，点击前往查阅 <i class="el-icon-right"></i>
                  </template>
                  <template v-else-if="step.status === 'in_progress' || step.status === 'processing'">
                    <i class="el-icon-loading" style="color: #409eff;"></i> <span style="color: #409eff;">正在汇总审核报告...</span>
                  </template>
                  <template v-else>
                    <i class="el-icon-data-line" style="color: #909399;"></i> <span style="color: #909399;">待执行报告生成</span>
                  </template>
                </div>
                
                <el-steps :active="step.status === 'done' ? (step.progress || 3) : (step.status === 'in_progress' || step.status === 'processing' ? 1 : 0)" finish-status="success" align-center>
                  <el-step v-for="(section, sIndex) in (step.details.sections || step.details.outline)" :key="sIndex" :title="section"></el-step>
                </el-steps>
              </div>

            </div>
          </el-collapse-item>
        </el-collapse>

        <div class="command-log-panel">
          <div class="command-log-header">
            <div class="command-log-title">
              <i class="el-icon-monitor"></i>
              <span>后端命令行实时日志</span>
              <el-tag size="mini" type="warning">{{ commandLogs.length }} 条</el-tag>
            </div>
            <div class="command-log-actions">
              <el-switch
                v-model="commandLogAutoScroll"
                active-text="自动滚动"
                inactive-text="暂停滚动"
                size="mini"
              ></el-switch>
              <el-button type="text" size="mini" @click="clearCommandLogs">清空</el-button>
            </div>
          </div>
          <div ref="commandLogList" class="command-log-list">
            <div
              v-for="(log, logIndex) in commandLogs"
              :key="logIndex"
              :class="['command-log-row', 'level-' + String(log.level || 'info').toLowerCase()]"
            >
              <span class="command-log-time">{{ log.time }}</span>
              <span class="command-log-level">{{ log.level }}</span>
              <span class="command-log-source">{{ log.logger }}</span>
              <span class="command-log-message">{{ log.message }}</span>
            </div>
            <div v-if="!commandLogs.length" class="command-log-empty">
              等待后端命令行输出；审核开始后会实时同步 logger / print / stderr 日志。
            </div>
          </div>
        </div>
      </div>

      <div v-show="currentPhase === 'result'" class="result-phase">
        <div v-if="finalReport && finalReport.summary">
          <div class="report-header">
            <h3>📊 审核报告</h3>
            <div class="score-badge">
              <el-progress type="circle" :percentage="finalReport.complianceScore" :width="80" :color="getScoreColor(finalReport.complianceScore)"></el-progress>
              <span class="score-label">合规评分</span>
            </div>
          </div>
          <div class="report-summary">
            <el-alert :title="finalReport.summary" type="info" :closable="false"></el-alert>
          </div>
          <div class="report-section" v-if="finalReport.compliantItems && finalReport.compliantItems.length">
            <h4>✅ 符合项</h4>
            <el-card v-for="(item, index) in finalReport.compliantItems" :key="'compliant-' + index" class="report-card compliant-card" shadow="hover">
              <div class="card-title">{{ item.title }}</div>
              <p class="card-description">{{ item.description }}</p>
              <el-tag size="mini" type="info">{{ item.reference }}</el-tag>
            </el-card>
          </div>
          <div class="report-section" v-if="finalReport.issues && finalReport.issues.length">
            <h4>⚠️ 需改进项</h4>
            <el-card v-for="(issue, index) in finalReport.issues" :key="'issue-' + index" :class="['report-card', 'issue-card', 'severity-' + issue.severity]" shadow="hover">
              <div class="card-header">
                <div class="card-title">{{ issue.title }}</div>
                <el-tag :type="getSeverityTagType(issue.severity)" size="small">优先级 {{ issue.priority }}</el-tag>
              </div>
              <p class="card-location">📍 {{ issue.location }}</p>
              <p class="card-description">{{ issue.description }}</p>
              <div class="card-suggestion">
                <el-tag size="mini" type="warning">建议</el-tag>
                <p>{{ issue.suggestion }}</p>
              </div>
            </el-card>
          </div>
          <div class="report-section" v-if="finalReport.recommendations && finalReport.recommendations.length">
            <h4>💡 改进建议</h4>
            <ul class="recommendations-list">
              <li v-for="(rec, index) in finalReport.recommendations" :key="'rec-' + index">{{ rec }}</li>
            </ul>
          </div>
          <div class="report-section risk-warning-section" v-if="finalReport.riskWarnings && finalReport.riskWarnings.length">
            <h4>🚨 风险预警</h4>
            <el-card v-for="(warn, index) in finalReport.riskWarnings" :key="'warn-' + index" class="report-card risk-warning-card" shadow="hover">
              <div class="card-header">
                <div class="card-title">{{ warn.title }}</div>
                <el-tag type="danger" size="small">高度预警</el-tag>
              </div>
              <p class="card-description warn-description">{{ warn.description }}</p>
              <div class="card-case-alert" v-if="warn.caseAlert">
                <el-tag size="mini" type="warning">案例警示</el-tag>
                <p>{{ warn.caseAlert }}</p>
              </div>
            </el-card>
          </div>
        </div>
        <el-empty v-else description="暂无审核报告数据"></el-empty>
      </div>
      
      <div v-show="currentPhase === 'optimization'" class="optimization-phase">
         <div v-if="rewrittenPlanData" class="opt-document-container">
            <div class="opt-doc-header">
              <h2>{{ rewrittenPlanData.rewrittenTitle || '优化后方案' }}</h2>
              <el-tag type="success" size="small"><i class="el-icon-check"></i> AI 重写完成</el-tag>
            </div>
            
            <div class="opt-doc-body">
              <div class="opt-highlights-box" v-if="rewrittenPlanData.highlights && rewrittenPlanData.highlights.length">
                <div class="highlight-title"><i class="el-icon-magic-stick"></i> 核心合规优化亮点：</div>
                <ul>
                  <li v-for="(hl, hIndex) in rewrittenPlanData.highlights" :key="hIndex">{{ hl }}</li>
                </ul>
              </div>
              
              <el-divider></el-divider>
              
              <div class="opt-dynamic-content" v-if="rewrittenPlanData.sections">
                <div v-for="(sec, sIndex) in rewrittenPlanData.sections" :key="'sec-' + sIndex" class="opt-section">
                  <h4>{{ sec.title }}</h4>
                  <p v-html="parseMarkdown(sec.content)"></p>
                </div>
              </div>
            </div>
         </div>
         <el-empty v-else description="暂无优化方案生成"></el-empty>
      </div>

    </div>
  </div>
</template>

<script>
import { FileText, GitBranch, ClipboardCheck, Sparkles } from 'lucide-vue'

export default {
  name: 'DocumentReviewPanel',
  components: {
    FileText,
    GitBranch,
    ClipboardCheck,
    Sparkles
  },
  props: {
    reviewData: {
      type: Object,
      default: () => ({})
    },
    fileName: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      phases: [
        { name: 'document', label: '文档预览', icon: 'FileText' },
        { name: 'workflow', label: '工作流程', icon: 'GitBranch' },
        { name: 'result', label: '审核报告', icon: 'ClipboardCheck' },
        { name: 'optimization', label: '方案优化', icon: 'Sparkles' }
      ],
      currentPhase: 'document',
      completedPhases: ['document'],
      isScanning: false,
      documentContent: '',
      documentInfo: {},
      workflowSteps: [],
      activeSteps: ['mcp-routing'],
      expandedServers: [],
      commandLogs: [],
      commandLogAutoScroll: true,
      maxCommandLogLines: 1000,
      finalReport: {},
      
      autoJumpTimer1: null,
      autoJumpTimer2: null
    }
  },
  computed: {
    workflowProgress() {
      if (!this.workflowSteps || this.workflowSteps.length === 0) return 0
      const completedCount = this.workflowSteps.filter(s => s.status === 'done').length
      return Math.round((completedCount / this.workflowSteps.length) * 100)
    },
    rewrittenPlanData() {
      if (!this.workflowSteps) return null;
      const rewriteStep = this.workflowSteps.find(step => step.id === 'plan-rewrite');
      return rewriteStep && rewriteStep.status === 'done' ? rewriteStep.details : null;
    }
  },
  watch: {
    reviewData: {
      immediate: true,
      deep: true,
      handler(newVal) {
        if (!newVal || Object.keys(newVal).length === 0) return;
        
        if (newVal.documentContent) this.documentContent = newVal.documentContent;
        if (newVal.workflow && newVal.workflow.steps) {
          this.initWorkflow(newVal.workflow.steps);
          this.markPhaseAsCompleted('workflow');
        }
        if (newVal.finalReport) {
          this.finalReport = newVal.finalReport;
          this.markPhaseAsCompleted('result');
        }
        const rewriteNode = (newVal.workflow?.steps || []).find(s => s.id === 'plan-rewrite');
        if (rewriteNode && rewriteNode.status === 'done') {
          this.markPhaseAsCompleted('optimization');
        }

        if (this.workflowProgress === 100) {
          this.triggerAutoJumpSequence();
        } else if (newVal.workflow && newVal.workflow.steps) {
           this.currentPhase = 'workflow';
        }
      }
    },
    workflowProgress(newVal) {
      if (newVal === 100) {
        this.triggerAutoJumpSequence();
      }
    },
    fileName: {
      immediate: true,
      handler(val) {
        if (val) this.$set(this.documentInfo, 'fileName', val);
      }
    }
  },
  beforeDestroy() {
    this.clearJumpTimers();
  },
  methods: {
    triggerAutoJumpSequence() {
      this.clearJumpTimers();

      this.autoJumpTimer1 = setTimeout(() => {
        if (this.completedPhases.includes('result')) {
          this.currentPhase = 'result';
          
          this.autoJumpTimer2 = setTimeout(() => {
            if (this.completedPhases.includes('optimization') && this.currentPhase === 'result') {
              this.currentPhase = 'optimization';
            }
          }, 2500);
          
        } else if (this.completedPhases.includes('optimization')) {
          this.currentPhase = 'optimization';
        }
      }, 800);
    },
    clearJumpTimers() {
      if (this.autoJumpTimer1) clearTimeout(this.autoJumpTimer1);
      if (this.autoJumpTimer2) clearTimeout(this.autoJumpTimer2);
    },
    parseMarkdown(text) {
      if (!text) return '';
      let parsedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      parsedText = parsedText.replace(/\n/g, '<br/>');
      return parsedText;
    },
    markPhaseAsCompleted(phaseName) {
      if (!this.completedPhases.includes(phaseName)) this.completedPhases.push(phaseName);
    },
    resetReviewState(initialPhase = 'document') {
      this.clearJumpTimers();
      this.currentPhase = initialPhase;
      this.completedPhases = [];
      this.isScanning = false;
      this.documentContent = '';
      this.documentInfo = {};
      this.workflowSteps = [];
      this.activeSteps = [];
      this.expandedServers = [];
      this.commandLogs = [];
      this.commandLogAutoScroll = true;
      this.finalReport = {};
      if (initialPhase) this.markPhaseAsCompleted(initialPhase);
    },
    updateDocumentContent(content) { this.documentContent = content },
    appendDocumentContent(content, documentInfo = {}) {
      if (content) this.documentContent += content;
      if (documentInfo && Object.keys(documentInfo).length) {
        Object.keys(documentInfo).forEach(key => this.$set(this.documentInfo, key, documentInfo[key]));
        if (documentInfo.filename) this.$set(this.documentInfo, 'fileName', documentInfo.filename);
      }
      this.markPhaseAsCompleted('document');
    },
    patchDocumentContent(content, documentInfo = {}) {
      this.documentContent = content || '';
      if (documentInfo && Object.keys(documentInfo).length) {
        Object.keys(documentInfo).forEach(key => this.$set(this.documentInfo, key, documentInfo[key]));
        if (documentInfo.filename) this.$set(this.documentInfo, 'fileName', documentInfo.filename);
      }
      this.markPhaseAsCompleted('document');
    },
    updateFileName(name) { this.$set(this.documentInfo, 'fileName', name) },
    startScanning() { this.isScanning = true },
    stopScanning() { this.isScanning = false },
    switchPhase(phase) {
      this.currentPhase = phase;
      this.markPhaseAsCompleted(phase);
    },
    initWorkflow(steps) {
      // 保留原始状态，如果不传默认置为 pending
      this.workflowSteps = steps.map(step => ({
        ...step,
        status: step.status || 'pending',
        logs: step.logs || []
      }))
    },
    patchWorkflowStep(stepId, patch = {}) {
      if (!stepId) return;
      const index = this.workflowSteps.findIndex(step => step.id === stepId);
      if (index === -1) return;

      const currentStep = this.workflowSteps[index];
      const updatedStep = {
        ...currentStep,
        ...patch,
        details: {
          ...(currentStep.details || {}),
          ...(patch.details || {})
        },
        logs: patch.logs || currentStep.logs || []
      };

      this.workflowSteps.splice(index, 1, updatedStep);

      if (patch.status === 'in_progress' || patch.status === 'processing') {
        if (!this.activeSteps.includes(stepId)) this.activeSteps.push(stepId);
      }

      if (patch.status === 'done') {
        this.markPhaseAsCompleted('workflow');
        if (stepId === 'plan-rewrite') this.markPhaseAsCompleted('optimization');
        if (stepId === 'report-generation') this.markPhaseAsCompleted('result');
      }
    },
    appendNodeLog(stepId, message) {
      if (!stepId || !message) return;
      const step = this.workflowSteps.find(item => item.id === stepId);
      if (!step) return;
      const logs = step.logs || [];
      this.patchWorkflowStep(stepId, {
        logs: [
          ...logs,
          {
            time: new Date().toLocaleTimeString(),
            message
          }
        ]
      });
      if (!this.activeSteps.includes(stepId)) {
        this.activeSteps.push(stepId);
      }
      this.$nextTick(() => {
        const lists = this.$el.querySelectorAll('.node-log-list');
        lists.forEach(list => {
          list.scrollTop = list.scrollHeight;
        });
      });
    },
    appendCommandLog(event = {}) {
      const message = event.message || event.content;
      if (!message) return;
      this.commandLogs.push({
        time: event.timestamp || new Date().toLocaleTimeString(),
        level: event.level || 'INFO',
        logger: event.logger || event.source || 'console',
        message
      });
      if (this.commandLogs.length > this.maxCommandLogLines) {
        this.commandLogs.splice(0, this.commandLogs.length - this.maxCommandLogLines);
      }
      if (this.commandLogAutoScroll) {
        this.$nextTick(() => {
          const list = this.$refs.commandLogList;
          if (list) list.scrollTop = list.scrollHeight;
        });
      }
    },
    clearCommandLogs() {
      this.commandLogs = [];
    },
    updateWorkflowStep(stepIndex, updates) {
  if (stepIndex >= 0 && stepIndex < this.workflowSteps.length) {
    // 1. 获取原始步骤数据，克隆一份以防引用污染
    let currentStep = { ...this.workflowSteps[stepIndex] };
    
    // 2. 核心逻辑：如果外层步骤标记为 'done'，强制同步其内部所有 server 的状态
    if (updates.status === 'done' && currentStep.details && currentStep.details.servers) {
      // 映射一个新的 servers 数组，确保 Vue 2 能检测到数组内部对象的变化
      currentStep.details.servers = currentStep.details.servers.map(server => ({
        ...server,
        status: server.status === 'pending' || server.status === 'processing' ? 'done' : server.status
      }));
    }

    // 3. 合并更新补丁
    const updatedStep = { ...currentStep, ...updates };

    // 4. 使用 splice 触发 Vue 2 的响应式系统更新视图
    this.workflowSteps.splice(stepIndex, 1, updatedStep);

    // 5. 自动展开逻辑
    if (updates.status === 'in_progress' || updates.status === 'processing') {
      const stepId = updatedStep.id;
      if (!this.activeSteps.includes(stepId)) {
        this.activeSteps.push(stepId);
      }
    }
  }
},
    updateFinalReport(report) { 
      this.finalReport = report;
      this.markPhaseAsCompleted('result');
    },
    patchFinalReport(snapshot = {}) {
      this.finalReport = {
        ...(this.finalReport || {}),
        ...snapshot,
        compliantItems: snapshot.compliantItems || this.finalReport.compliantItems || [],
        issues: snapshot.issues || this.finalReport.issues || [],
        recommendations: snapshot.recommendations || this.finalReport.recommendations || [],
        riskWarnings: snapshot.riskWarnings || this.finalReport.riskWarnings || []
      };
      this.markPhaseAsCompleted('result');
    },
    appendReportChunk(section, content) {
      if (!content) return;
      if (!this.finalReport) this.finalReport = {};
      if (!this.finalReport.rawReport) this.$set(this.finalReport, 'rawReport', '');
      this.finalReport.rawReport += content;
      if (section === 'summary') {
        const oldSummary = this.finalReport.summary || '';
        this.$set(this.finalReport, 'summary', oldSummary + content);
      }
      if (!this.finalReport.complianceScore) this.$set(this.finalReport, 'complianceScore', 80);
      this.markPhaseAsCompleted('result');
    },
    appendReportItem(section, item) {
      if (!section || !item) return;
      if (!this.finalReport[section]) this.$set(this.finalReport, section, []);
      this.finalReport[section].push(item);
      this.markPhaseAsCompleted('result');
    },
    appendOptimizationChunk(event) {
      const stepId = 'plan-rewrite';
      const index = this.workflowSteps.findIndex(step => step.id === stepId);
      if (index === -1) return;
      const step = this.workflowSteps[index];
      const details = step.details || {};
      const sections = [...(details.sections || [])];
      sections.push({
        title: event.section || '优化建议',
        content: event.content || ''
      });
      this.patchWorkflowStep(stepId, {
        status: 'in_progress',
        details: {
          ...details,
          sections
        }
      });
    },
    isPhaseCompleted(index) { return this.completedPhases.includes(this.phases[index].name) },
    handleTabClick(phaseName) {
      this.currentPhase = phaseName;
    },
    toggleServer(index) {
      const i = this.expandedServers.indexOf(index);
      if (i > -1) this.expandedServers.splice(i, 1);
      else this.expandedServers.push(index);
    },
    getScoreColor(score) {
      if (score >= 90) return '#67c23a';
      if (score >= 70) return '#e6a23c';
      return '#f56c6c';
    },
    getSeverityTagType(severity) {
      const types = { high: 'danger', medium: 'warning', low: 'info' };
      return types[severity] || 'info';
    }
  }
}
</script>

<style scoped>
.document-review-panel { height: 100%; display: flex; flex-direction: column; background: transition; overflow: hidden; }

/* ======== Tabs ======== */
.phase-tabs {
  display: flex;
  background: #FDFBF9;
  border-bottom: 1px solid #E5E0DA;
  height: 64px;
  padding: 0 14px;
}
.phase-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 100%;
  cursor: pointer;
  transition: background-color 0.3s ease, color 0.3s ease;
  color: #7a6850;
  font-size: 14px;
  font-weight: 500;
  letter-spacing: 0.5px;
  position: relative;
  border-radius: 12px 12px 0 0;
}
.phase-tab:hover:not(.active) {
  color: #5c4632;
  background: #F4ECE4;
}
.phase-tab.active {
  color: #4A2F1B;
  font-weight: 700;
  background: #ffffff;
}
.phase-tab.active::after {
  content: '';
  position: absolute;
  left: 50%;
  bottom: 0;
  width: 42px;
  height: 3px;
  border-radius: 999px;
  background: #6B3F24;
  transform: translateX(-50%);
}
.phase-icon {
  color: currentColor;
  flex-shrink: 0;
}
.phase-content { flex: 1; overflow-y: auto; padding: 20px; background: #ffffff; }

/* ======== 文档预览 ======== */
.document-phase { height: 100%; display: flex; flex-direction: column; }
.document-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.document-header h3 { margin: 0; font-size: 16px; color: #E47728; font-weight: 600; }
.document-content-wrapper {
  flex: 1;
  overflow: hidden;
  border: 1px solid #E8D5C4;
  border-radius: 12px;
  position: relative;
  background: linear-gradient(135deg, #FFFDF7 0%, #FFF9E6 100%);
  box-shadow: 0 4px 12px rgba(139, 69, 19, 0.05);
}
.document-content {
  height: 100%;
  overflow-y: auto;
  padding: 16px;
  background: #ffffff;
  position: relative;
  margin: 8px;
  border-radius: 12px;
}
.document-content pre { margin: 0; font-family: 'Courier New', monospace; font-size: 13px; line-height: 1.8; white-space: pre-wrap; color: #303133; }
.document-content.scanning { overflow: hidden; position: relative; }
.scan-line { position: absolute; left: 0; right: 0; height: 2px; background: linear-gradient(90deg, transparent, #F6A55A, transparent); box-shadow: 0 0 10px #F6A55A; animation: scan 2s linear infinite; z-index: 10; }
@keyframes scan { 0% { top: 0; } 100% { top: 100%; } }
.review-upload-action {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
}
.review-upload-btn {
  min-width: 132px;
  height: 42px;
  border: none;
  border-radius: 12px;
  background: #F2994A;
  color: #fff;
  font-weight: 600;
  box-shadow: 0 8px 18px rgba(242, 153, 74, 0.22);
}
.review-upload-btn:hover,
.review-upload-btn:focus {
  background: #E88935;
  color: #fff;
}
.scanning-status {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 10px 12px;
  background: linear-gradient(135deg, #FFF9E6 0%, #FFFDF7 100%);
  border: 1px solid #E8D5C4;
  border-radius: 12px;
  color: #E47728;
  font-size: 14px;
}

/* ======== 工作流阶段 ======== */
.workflow-header-card {
  background: linear-gradient(135deg, #FFFDF7 0%, #FFF9E6 100%);
  padding: 20px 20px 16px 20px;
  border: 1px solid #E8D5C4;
  border-bottom: none;
  border-radius: 12px 12px 0 0;
  box-shadow: 0 4px 12px rgba(139, 69, 19, 0.05);
}
.workflow-title-row { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; }
.title-icon { font-size: 18px; color: #E47728; }
.title-text { font-size: 15px; font-weight: 600; color: #E47728; }
.custom-progress ::v-deep .el-progress__text { font-size: 13px !important; color: #E47728; }
.custom-progress ::v-deep .el-progress-bar__inner { background: linear-gradient(90deg, #F6A55A, #E47728); }

.flat-workflow-steps {
  border-top: none;
  background: #ffffff;
  border: 1px solid #E8D5C4;
  border-top: 1px dashed #E8D5C4;
  border-radius: 0 0 12px 12px;
  box-shadow: 0 4px 12px rgba(139, 69, 19, 0.05);
}
.command-log-panel {
  margin-top: 16px;
  border: 1px solid #E8D5C4;
  border-radius: 12px;
  background: #111827;
  box-shadow: 0 4px 12px rgba(139, 69, 19, 0.05);
  overflow: hidden;
}
.command-log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: linear-gradient(90deg, #FFFDF7 0%, #FFF9E6 100%);
  border-bottom: 1px solid #FDE2BE;
}
.command-log-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: #E47728;
}
.command-log-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.command-log-actions ::v-deep .el-switch__label {
  color: #B07A43;
  font-size: 12px;
}
.command-log-list {
  height: 260px;
  overflow-y: auto;
  padding: 12px 14px;
  font-family: Consolas, Monaco, 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.7;
  background: #111827;
  color: #d1d5db;
}
.command-log-row {
  display: grid;
  grid-template-columns: 72px 58px 136px minmax(0, 1fr);
  gap: 8px;
  align-items: start;
  padding: 2px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}
.command-log-time { color: #9ca3af; }
.command-log-level {
  color: #93c5fd;
  font-weight: 700;
}
.command-log-source {
  color: #fbbf24;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.command-log-message {
  white-space: pre-wrap;
  word-break: break-word;
  color: #e5e7eb;
}
.command-log-row.level-warning .command-log-level,
.command-log-row.level-warn .command-log-level { color: #f59e0b; }
.command-log-row.level-error .command-log-level,
.command-log-row.level-critical .command-log-level { color: #f87171; }
.command-log-row.level-debug .command-log-level { color: #a78bfa; }
.command-log-empty {
  color: #9ca3af;
  padding: 18px 4px;
  text-align: center;
}
.flat-workflow-steps ::v-deep .el-collapse-item__header {
  border-bottom: 1px solid #FFF9E6;
  padding: 0 20px;
  height: 60px;
  line-height: 60px;
  background-color: transparent;
  transition: all 0.3s;
}
.flat-workflow-steps ::v-deep .el-collapse-item__header:hover {
  background: linear-gradient(90deg, #FFFDF7 0%, transparent 100%);
}
.flat-workflow-steps ::v-deep .el-collapse-item__arrow { display: none; }
.flat-workflow-steps ::v-deep .el-collapse-item__wrap {
  border-bottom: 1px solid #FFF9E6;
  background-color: transparent;
}
.flat-workflow-steps ::v-deep .el-collapse-item__content { padding-bottom: 0; }

.step-title-bar { display: flex; justify-content: space-between; align-items: center; width: 100%; }
.step-left { display: flex; align-items: center; gap: 12px; }
.step-icon { font-size: 18px; filter: drop-shadow(0 1px 2px rgba(228, 119, 40, 0.2)); }
.step-name { font-size: 14px; color: #E47728; font-weight: 600; }
.step-right { display: flex; align-items: center; gap: 10px; }
.log-count-badge { margin-right: 2px; }

/* 状态文字样式 */
.status-text { font-size: 13px; display: flex; align-items: center; gap: 4px; font-weight: 500; }
.status-text.success { color: #52c41a; }
.status-text.pending { color: #d4b895; }
.status-text.processing { color: #F6A55A; }
.text-disabled { color: #d4b895; }
.text-processing { color: #F6A55A; }
.text-pending { color: #d4b895; }
.text-pending-italic { color: #d4b895; font-style: italic; margin: 0; font-size: 12px;}

.collapse-arrow { font-size: 12px; color: #E47728; transition: transform 0.3s; }
.el-collapse-item.is-active .collapse-arrow { transform: rotate(180deg); }
.step-detail-content {
  padding: 16px 20px 20px 52px;
  background: linear-gradient(135deg, #FFFDF7 0%, #ffffff 100%);
  border-left: 3px solid #FDE2BE;
  margin: 0 12px 12px 12px;
  border-radius: 0 0 6px 6px;
}
.node-log-panel {
  margin-bottom: 14px;
  padding: 12px;
  border: 1px solid #FDE2BE;
  border-radius: 8px;
  background: #FFFDF7;
}
.node-log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  font-size: 13px;
  font-weight: 700;
  color: #E47728;
}
.node-log-header i { margin-right: 6px; }
.node-log-subtitle {
  font-size: 12px;
  font-weight: 400;
  color: #B07A43;
}
.node-log-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 180px;
  overflow-y: auto;
}
.node-log-row {
  display: flex;
  gap: 8px;
  font-size: 12px;
  line-height: 1.6;
  color: #303133;
}
.node-log-time {
  color: #909399;
  flex-shrink: 0;
  font-family: Consolas, Monaco, monospace;
}
.node-log-message {
  white-space: pre-wrap;
  word-break: break-word;
}
.node-log-empty {
  font-size: 12px;
  color: #B07A43;
  line-height: 1.6;
}

.clickable-box {
  cursor: pointer;
  transition: all 0.3s;
  background: linear-gradient(135deg, #FFF9E6 0%, #FFFDF7 100%);
  border: 2px dashed #FDE2BE;
  border-radius: 6px;
  padding: 12px;
}
.clickable-box:hover {
  box-shadow: 0 4px 16px rgba(246, 165, 90, 0.25);
  transform: translateY(-2px);
  border-color: #F6A55A;
  background: linear-gradient(135deg, #FFF9E6 0%, #ffffff 100%);
}

/* ======== MCP Server 交互 ======== */
.mcp-servers-list {
  background: linear-gradient(135deg, #FFFDF7 0%, #ffffff 100%);
  border: 1px solid #FDE2BE;
  border-radius: 6px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.mcp-server-container {
  background: #ffffff;
  border: 1px solid #FFF9E6;
  border-radius: 6px;
  overflow: hidden;
  transition: all 0.3s;
}
.mcp-server-container:hover {
  box-shadow: 0 2px 8px rgba(246, 165, 90, 0.15);
}
.mcp-server-container:last-child { border-bottom: none; }

/* 计算校验Server 高亮样式 */
.mcp-server-container.calc-server-highlight {
  background: linear-gradient(to right, #fff7e6 0%, transparent 100%);
  border-left: 3px solid #fa8c16;
  padding-left: 8px;
  margin: 8px 0;
  border-radius: 4px;
}

/* 合规审查Server 高亮样式 */
.mcp-server-container.compliance-server-highlight {
  background: linear-gradient(to right, #fdf6ea 0%, transparent 100%);
  border-left: 3px solid #eeb67a;
  padding-left: 8px;
  margin: 8px 0;
  border-radius: 6px;
}

.mcp-server-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px;
  cursor: pointer;
  transition: all 0.3s;
  background: linear-gradient(90deg, #FFFDF7 0%, #ffffff 100%);
}
.mcp-server-row:hover {
  background: linear-gradient(90deg, #FFF9E6 0%, #FFFDF7 100%);
  padding-left: 18px;
}
.server-left { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.server-icon { font-size: 16px; filter: drop-shadow(0 1px 2px rgba(228, 119, 40, 0.2)); }
.server-name { font-size: 13px; color: #E47728; font-weight: 600; display: flex; align-items: center; gap: 6px; }
.server-right { font-size: 13px; display: flex; align-items: center; }
.server-arrow { font-size: 13px; color: #F6A55A; transition: transform 0.3s; }
.server-details-content {
  padding: 12px 16px 16px 16px;
  background: linear-gradient(135deg, #FFF9E6 0%, #FFFDF7 100%);
  border-top: 1px dashed #FDE2BE;
  margin: 0 8px 8px 8px;
  border-radius: 0 0 6px 6px;
}

/* 计算校验Server 内容样式 */
.server-details-content.calc-server-content {
  background-color: #FFFDF7;
  border: 2px solid #FDE2BE;
  border-radius: 4px;
  padding: 15px;
}

.calc-server-results {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.calc-card {
  background-color: #ffffff;
  border: 2px solid #F6A55A;
  border-radius: 8px;
  padding: 15px;
}

.calc-card-header {
  display: flex;
  align-items: center;
  color: #E47728;
  font-weight: bold;
  font-size: 15px;
  margin-bottom: 15px;
}

.calc-icon-warning {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  width: 18px;
  height: 18px;
  border: 1.5px solid #F5A623;
  border-radius: 50%;
  margin-right: 8px;
  font-size: 12px;
  font-weight: bold;
  color: #F5A623;
}

.calc-card-title {
  font-size: 15px;
  font-weight: 600;
  color: #E47728;
}

.calc-section {
  margin-bottom: 12px;
}

.calc-section:last-child {
  margin-bottom: 0;
}

.calc-label {
  font-size: 12px;
  color: #888888;
  margin-bottom: 6px;
}

.calc-box-warning {
  background-color: #F8F9FA;
  min-height: 40px;
  border-radius: 4px;
  padding: 10px 12px;
  font-size: 13px;
  color: #333333;
  line-height: 1.5;
}

.calc-box-formula-wrapper {
  border: 1px dotted #dddddd;
  padding: 8px;
  border-radius: 4px;
}

.calc-box-formula-inner {
  background-color: #FFF9E6;
  color: #E47728;
  font-size: 13px;
  padding: 8px 10px;
  border-radius: 2px;
  font-family: 'Courier New', Consolas, monospace;
  line-height: 1.5;
}

.calc-box-suggestion {
  background-color: #FFF3EB;
  border: 1px dotted #FCDFC9;
  padding: 10px;
  border-radius: 4px;
}

.calc-suggestion-label {
  font-size: 12px;
  color: #FF9E79;
  margin-bottom: 4px;
}

.calc-suggestion-content {
  color: #E47728;
  font-size: 13px;
  line-height: 1.5;
}

/* 合规审查Server 内容样式 */
.server-details-content.compliance-server-content {
  background: #ffffff;
  border: 2px solid #eeb67a;
  border-radius: 6px;
  padding: 20px 16px;
}

.compliance-result-item {
  background: white;
  padding: 20px 16px;
  border-radius: 6px;
  margin-bottom: 12px;
  border-left: none;
  border: 2px solid #eeb67a;
  box-shadow: 0 2px 8px rgba(238, 182, 122, 0.15);
}

.compliance-result-item:last-child { margin-bottom: 0; }

.compliance-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding-bottom: 0;
  border-bottom: none;
}

.compliance-header i.el-icon-office-building {
  font-size: 20px;
  color: #df7a28;
}

.compliance-title-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.compliance-title {
  font-size: 16px;
  font-weight: bold;
  color: #df7a28;
}

.compliance-subtitle {
  font-size: 12px;
  color: #666666;
  font-weight: 400;
}

.compliance-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.company-info-box {
  background: #f9f9f9;
  padding: 12px 16px;
  border-radius: 4px;
  border: none;
  display: flex;
  align-items: center;
  gap: 16px;
}

.info-label {
  font-size: 14px;
  color: #666666;
  font-weight: normal;
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}

.info-label i {
  color: #666666;
}

.info-value {
  font-size: 14px;
  color: #333333;
  font-weight: bold;
  flex: 1;
}

.compliance-detail {
  font-size: 14px;
  color: #333333;
  line-height: 1.6;
  background: #f9f9f9;
  padding: 12px 16px;
  border-radius: 4px;
}

.compliance-check-items {
  background: #fff;
  padding: 16px;
  border-radius: 4px;
  border: 1px solid #f2c7c9;
  margin-top: 16px;
  margin-bottom: 16px;
}

.check-items-label {
  font-size: 14px;
  color: #666666;
  margin-bottom: 12px;
  font-weight: normal;
}

.check-items-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.check-item-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0;
  background: #f9f9f9;
  border-radius: 4px;
  height: 24px;
  padding: 0 8px;
}

.check-icon-pass {
  color: #52c41a;
  font-size: 16px;
}

.check-icon-fail {
  color: #f5222d;
  font-size: 16px;
}

.check-item-name {
  flex: 1;
  font-size: 13px;
  color: #303133;
  font-weight: 500;
}

.check-item-result {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 3px;
}

.result-pass {
  color: #52c41a;
  background: #f6ffed;
  border: 1px solid #b7eb8f;
}

.result-fail {
  color: #f5222d;
  background: #fff1f0;
  border: 1px solid #ffccc7;
}

.risk-assessment {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0;
  background: #fdf6ea;
  border-radius: 4px;
  height: 48px;
  padding: 0 12px;
  margin-bottom: 12px;
}

.risk-label {
  font-size: 12px;
  color: #8c8c8c;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 4px;
}

.risk-label i {
  color: #fa8c16;
}

.risk-desc {
  flex: 1;
  font-size: 12px;
  color: #595959;
  margin-left: 4px;
}

.compliance-suggestion {
  margin-top: 4px;
}

.compliance-suggestion ::v-deep .el-alert {
  padding: 10px 12px;
}

.compliance-suggestion ::v-deep .el-alert__title {
  font-size: 13px;
  line-height: 1.6;
}

/* 普通Server样式保持不变 */
.res-item { margin-bottom: 10px; }
.res-item:last-child { margin-bottom: 0; }
.res-title { font-size: 12px; font-weight: bold; color: #409eff; margin-bottom: 4px; }
.res-desc { font-size: 12px; color: #606266; line-height: 1.5; }

/* ======== 其他小组件 ======== */
.schema-fields { margin-top: 4px; }
.query-list { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px;}
.alignment-box { display: flex; flex-direction: column; gap: 10px; margin-top: 8px;}
.channel-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.quality-check-box { display: flex; flex-direction: column; gap: 8px; margin-top: 8px;}
.check-item { display: flex; gap: 10px; background: #fff; padding: 10px; border-radius: 4px; border-left: 3px solid #67c23a; border-right: 1px solid #ebeef5; border-top: 1px solid #ebeef5; border-bottom: 1px solid #ebeef5;}
.text-success { color: #67c23a; margin-top: 2px;}
.rewrite-box { background: #f0f9ff; padding: 12px 16px; border-radius: 4px; }
.rewrite-header { font-weight: 600; font-size: 13px; display: flex; justify-content: space-between; align-items: center; color: #409eff;}
.comparison { display: flex; gap: 12px; align-items: center; margin: 8px 0; }
.source-info { flex: 1; padding: 8px; background: white; border: 1px solid #ebeef5; border-radius: 4px; font-size: 12px; }
.conclusion { padding: 8px; background: #f0f9eb; border-radius: 4px; font-size: 12px; }
.generation-info { padding: 16px; background: #f0f9ff; border-radius: 4px; border: 1px solid #c6e2ff;}
.generation-title { margin-bottom: 12px; font-size: 13px; color: #409eff; font-weight: 500; display: flex; align-items: center; justify-content: space-between; }
.step-logs { margin-top: 12px; padding: 10px; border: 1px solid #FDE2BE; border-radius: 6px; background: #FFFDF7; }
.step-logs-title { font-size: 13px; font-weight: bold; color: #E47728; margin-bottom: 8px; }
.step-log-item { display: flex; gap: 8px; font-size: 12px; line-height: 1.6; color: #606266; }
.log-time { color: #909399; flex-shrink: 0; }
.log-message { color: #303133; }

/* ======== 审核报告 ======== */
.result-phase {
  height: 100%;
  overflow-y: auto;
  background: linear-gradient(135deg, #FFFDF7 0%, #ffffff 100%);
  padding: 20px;
  border-radius: 6px;
  border: 2px solid #FDE2BE;
}
.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 2px solid #FDE2BE;
}
.report-header h3 { margin: 0; font-size: 18px; color: #E47728; font-weight: 600; }
.score-badge { display: flex; flex-direction: column; align-items: center; gap: 8px; }
.score-label { font-size: 12px; color: #E47728; font-weight: 500; }
.report-summary { margin-bottom: 24px; }
.report-section { margin-bottom: 24px; }
.report-section h4 { margin: 0 0 12px 0; font-size: 16px; color: #E47728; font-weight: 600; }
.report-card {
  margin-bottom: 12px;
  padding: 16px;
  background: #ffffff;
  border: 1px solid #FFF9E6;
  border-radius: 6px;
  transition: all 0.3s;
}
.report-card:hover {
  box-shadow: 0 2px 8px rgba(246, 165, 90, 0.15);
  border-color: #FDE2BE;
}
.card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; }
.card-title { font-weight: 600; font-size: 14px; color: #E47728; margin-bottom: 8px; }
.card-location { margin: 0 0 8px 0; font-size: 12px; color: #909399; }
.card-description { margin: 0 0 8px 0; font-size: 13px; color: #606266; line-height: 1.6; }
.card-suggestion { margin-top: 12px; padding-top: 12px; border-top: 1px dashed #FDE2BE; }
.card-suggestion p { margin: 8px 0 0 0; font-size: 13px; color: #606266; line-height: 1.6; }
.compliant-card { border-left: 3px solid #67c23a; }
.issue-card { border-left: 3px solid #F6A55A; }
.issue-card.severity-high { border-left-color: #f56c6c; }
.issue-card.severity-low { border-left-color: #d4b895; }
.recommendations-list { margin: 0; padding-left: 24px; }
.recommendations-list li { margin-bottom: 8px; font-size: 14px; line-height: 1.6; color: #606266; }
.risk-warning-section h4 { color: #c0392b; }
.risk-warning-card { border-left: 4px solid #f56c6c; background: #fff8f8; }
.warn-description { color: #333; font-size: 14px; line-height: 1.7; margin: 8px 0; }
.card-case-alert { margin-top: 10px; padding: 10px 12px; background: #fff3cd; border-radius: 4px; border-left: 3px solid #e6a817; }
.card-case-alert p { margin: 6px 0 0 0; font-size: 13px; color: #7d5a00; line-height: 1.6; }

/* ======== 方案优化排版 ======== */
.optimization-phase {
  background: linear-gradient(135deg, #FFFDF7 0%, #ffffff 100%);
  padding: 20px;
  border-radius: 6px;
  border: 2px solid #FDE2BE;
  height: 100%;
  overflow-y: auto;
}
.opt-document-container {
  max-width: 900px;
  margin: 0 auto;
  background: #ffffff;
  padding: 40px 60px;
  border-radius: 4px;
  box-shadow: 0 0 10px rgba(246, 165, 90, 0.05);
  border: 1px solid #FDE2BE;
}
.opt-doc-header {
  text-align: center;
  margin-bottom: 16px;
}
.opt-doc-header h2 {
  font-size: 24px;
  color: #262626;
  margin: 0 0 16px 0;
  line-height: 1.4;
  font-weight: 600;
}
.ai-badge-container {
  text-align: center;
  margin-bottom: 30px;
}
.ai-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background-color: #FFF9E6;
  color: #E47728;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 500;
  border: 1px solid #FDE2BE;
}
.opt-highlights-box {
  background-color: #FFF9E6;
  border: 1px solid #FDE2BE;
  border-radius: 6px;
  padding: 20px 24px;
  margin-bottom: 30px;
}
.highlight-title {
  color: #E47728;
  font-weight: 600;
  font-size: 15px;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.opt-highlights-box ul {
  margin: 0;
  padding-left: 20px;
  font-size: 14px;
  color: #595959;
  line-height: 2;
}
.opt-highlights-box ul li {
  margin-bottom: 4px;
  list-style-type: disc;
  color: #8c8c8c;
}
.opt-highlights-box ul li span {
  color: #595959;
}

.opt-divider {
  height: 1px;
  background-color: #f0f0f0;
  border: none;
  margin: 30px 0;
}

.opt-dynamic-content {
  margin-top: 0;
  line-height: 1.8;
}
.opt-section {
  margin-bottom: 24px;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 0;
}
.opt-section h4 {
  font-size: 18px;
  color: #262626;
  margin: 24px 0 16px 0;
  font-weight: bold;
}
.opt-section ::v-deep p {
  font-size: 15px;
  color: #595959;
  line-height: 1.8;
  margin: 0 0 16px 0;
  text-align: justify;
}
.opt-section ::v-deep strong {
  color: #262626;
  font-weight: 600;
}
</style>
