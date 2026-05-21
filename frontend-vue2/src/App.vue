<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  width: 100%;
  height: 100%;
  font-family: 'Times New Roman', 'PingFang SC', 'Microsoft YaHei', serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

:root {
  --mota-radius: 12px;
  --mota-soft-border: #E8D5C4;
  --mota-paper-shadow: 0 4px 12px rgba(139, 69, 19, 0.05);
}

.el-button:not(.is-circle),
.el-input__inner,
.el-textarea__inner,
.el-card,
.el-dialog,
.el-message,
.el-alert,
.el-tag {
  border-radius: var(--mota-radius) !important;
}

.el-button:not(.is-circle),
.el-input__inner,
.el-textarea__inner,
.el-card {
  border-color: var(--mota-soft-border) !important;
}

.el-card {
  box-shadow: var(--mota-paper-shadow) !important;
}

.agent-thinking,
.global-search,
.history-list,
.knowledge-manager,
.file-preview,
.document-review-panel .document-content-wrapper,
.document-review-panel .document-content,
.document-review-panel .workflow-header-card,
.document-review-panel .flat-workflow-steps,
.document-review-panel .command-log-panel,
.document-review-panel .node-log-panel,
.document-review-panel .report-card,
.document-review-panel .opt-document-container,
.document-review-panel .opt-highlights-box,
.document-review-panel .generation-info,
.document-review-panel .rewrite-box,
.document-review-panel .check-item,
.document-review-panel .step-logs,
.message-bubble,
.input-wrapper,
.file-preview-list,
.file-item,
.workflow-step,
.step-details,
.details-section,
.unsupported-preview,
.txt-preview {
  border-radius: var(--mota-radius) !important;
}

.agent-thinking,
.global-search,
.history-list,
.document-review-panel .document-content-wrapper,
.document-review-panel .workflow-header-card,
.document-review-panel .flat-workflow-steps,
.document-review-panel .command-log-panel,
.document-review-panel .node-log-panel,
.document-review-panel .report-card,
.document-review-panel .generation-info,
.document-review-panel .step-logs,
.input-wrapper,
.file-preview-list,
.file-item,
.workflow-step,
.step-details,
.unsupported-preview,
.txt-preview {
  border-color: var(--mota-soft-border) !important;
}
</style>
