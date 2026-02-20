<template>
  <div class="review-report">
    <div class="header">
      <h3>📊 合规审查报告</h3>
      <el-tag type="danger" size="medium">D 级 - 高风险</el-tag>
    </div>

    <el-alert
      title="发现 2 项违规条款"
      type="error"
      :closable="false"
      show-icon
      class="summary-alert"
    >
    </el-alert>

    <div class="findings">
      <h4>🔍 详细分析</h4>

      <el-card class="finding-card" shadow="hover">
        <div slot="header">
          <el-tag type="danger" size="small">违规 #1</el-tag>
          <span class="finding-title">用人单位随时解除劳动合同条款</span>
        </div>

        <div class="finding-content">
          <p><strong>问题位置:</strong> 第三章第三十九条</p>
          <p><strong>法律依据:</strong> 《劳动合同法》第三十九条规定了用人单位可以解除劳动合同的情形，
            但必须符合法定条件，不得滥用权利。</p>
          <p><strong>风险评估:</strong> <el-tag type="danger" size="mini">高风险</el-tag>
            该条款可能导致劳动者权益受损，存在被认定为无效条款的风险。</p>
        </div>
      </el-card>

      <el-card class="finding-card" shadow="hover">
        <div slot="header">
          <el-tag type="warning" size="small">违规 #2</el-tag>
          <span class="finding-title">缺少劳动者权利保障条款</span>
        </div>

        <div class="finding-content">
          <p><strong>问题位置:</strong> 全文</p>
          <p><strong>法律依据:</strong> 《劳动合同法》要求劳动合同应当明确劳动者的权利和义务。</p>
          <p><strong>风险评估:</strong> <el-tag type="warning" size="mini">中风险</el-tag>
            合同内容不完整，可能导致争议。</p>
        </div>
      </el-card>
    </div>

    <div class="recommendations">
      <h4>💡 AI 修改建议</h4>

      <ol class="suggestion-list">
        <li>
          <strong>修改第三十九条:</strong> 增加"符合法定条件"的限定，明确解除劳动合同
          的具体情形和程序。
        </li>
        <li>
          <strong>增加劳动者权利条款:</strong> 明确劳动者享有的休息休假、劳动报酬、
          社会保险等权利。
        </li>
        <li>
          <strong>完善争议解决机制:</strong> 增加劳动争议解决的途径和程序说明。
        </li>
      </ol>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ReviewReport'
}
</script>

<style scoped>
.review-report {
  height: 100%;
  overflow-y: auto;
  padding-bottom: 20px;
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

.summary-alert {
  margin-bottom: 24px;
}

.findings h4,
.recommendations h4 {
  color: #374151;
  font-size: 16px;
  margin: 24px 0 12px 0;
}

.finding-card {
  margin-bottom: 16px;
}

.finding-title {
  margin-left: 8px;
  font-weight: 500;
}

.finding-content {
  font-size: 14px;
  line-height: 1.8;
}

.finding-content p {
  margin: 8px 0;
  color: #6b7280;
}

.suggestion-list {
  padding-left: 20px;
}

.suggestion-list li {
  margin: 12px 0;
  color: #6b7280;
  line-height: 1.6;
}
</style>
