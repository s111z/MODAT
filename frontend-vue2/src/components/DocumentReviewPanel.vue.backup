<template>
  <div class="document-review-panel">
    <el-tabs v-model="currentPhase" @tab-click="handlePhaseChange">
      <el-tab-pane label="📄 文档预览" name="document">
        <DocumentViewer />
      </el-tab-pane>
      <el-tab-pane label="⚙️ 工作流程" name="workflow">
        <AgentThinking />
      </el-tab-pane>
      <el-tab-pane label="📊 审核报告" name="result">
        <ReviewReport />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script>
import { mapState, mapMutations } from 'vuex'
import AgentThinking from './AgentThinking.vue'
import DocumentViewer from './DocumentViewer.vue'
import ReviewReport from './ReviewReport.vue'

export default {
  name: 'DocumentReviewPanel',
  components: {
    AgentThinking,
    DocumentViewer,
    ReviewReport
  },
  computed: {
    ...mapState(['reviewPhase']),
    currentPhase: {
      get() {
        return this.reviewPhase
      },
      set(value) {
        this.SET_REVIEW_PHASE(value)
      }
    }
  },
  methods: {
    ...mapMutations(['SET_REVIEW_PHASE']),
    handlePhaseChange(tab) {
      this.SET_REVIEW_PHASE(tab.name)
    }
  }
}
</script>

<style scoped>
.document-review-panel {
  height: 100%;
  padding: 20px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}
</style>
