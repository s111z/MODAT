<template>
  <div class="document-viewer">
    <div class="header">
      <h3>📄 文档预览</h3>
      <el-tag type="success" size="small">已上传</el-tag>
    </div>

    <el-card class="document-card">
      <div slot="header">
        <div class="doc-info">
          <span><strong>文件名:</strong> 联邦劳动法.pdf</span>
          <span><strong>大小:</strong> 2.4 MB</span>
          <span><strong>状态:</strong> <el-tag size="mini" type="success">待审核</el-tag></span>
        </div>
      </div>

      <div class="document-content">
        <h4>第一章 总则</h4>
        <p>
          第一条 为了完善劳动合同制度，明确劳动合同双方当事人的权利和义务，
          保护劳动者的合法权益，构建和发展和谐稳定的劳动关系，制定本法。
        </p>

        <p>
          第二条 中华人民共和国境内的企业、个体经济组织、民办非企业单位等组织
          (以下称用人单位)与劳动者建立劳动关系，订立、履行、变更、解除或者终止
          劳动合同，适用本法。
        </p>

        <div class="highlight-section">
          <h4>⚠️ 风险条款</h4>
          <p class="risk-text">
            第三十九条 <span class="highlight">用人单位可以随时解除劳动合同</span>
            的情形包括：劳动者严重违反规章制度、严重失职等。
          </p>
        </div>

        <p>
          第四条 用人单位应当依法建立和完善劳动规章制度，保障劳动者享有劳动权利、
          履行劳动义务。
        </p>
      </div>
    </el-card>
  </div>
</template>

<script>
export default {
  name: 'DocumentViewer'
}
</script>

<style scoped>
.document-viewer {
  height: 100%;
  overflow-y: auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header h3 {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.doc-info {
  display: flex;
  gap: 20px;
  font-size: 14px;
}

.document-content {
  padding: 16px;
  line-height: 1.8;
}

.document-content h4 {
  color: #374151;
  margin: 16px 0 8px 0;
}

.document-content p {
  color: #6b7280;
  margin: 8px 0;
}

.highlight-section {
  background: #fef3c7;
  border: 1px solid #fbbf24;
  border-radius: 4px;
  padding: 12px;
  margin: 16px 0;
}

.risk-text {
  color: #92400e;
}

.highlight {
  background: #fee2e2;
  color: #991b1b;
  padding: 2px 4px;
  border-radius: 2px;
  font-weight: 600;
}
</style>
