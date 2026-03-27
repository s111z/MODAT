<template>
  <div class="file-preview">
    <!-- 未选择文件 -->
    <div v-if="!file" class="empty-preview">
      <i class="el-icon-document-copy empty-icon"></i>
      <p>请从左侧选择文件进行预览</p>
    </div>

    <!-- 已选择文件 -->
    <template v-else>
      <!-- 顶部文件信息栏 -->
      <div class="preview-header">
        <div class="file-title">
          <i :class="getFileIcon(file.ext)"></i>
          <span :title="file.filename">{{ file.filename }}</span>
        </div>
        <div class="header-actions">
          <el-tag size="small" :type="getExtTagType(file.ext)">{{ file.ext }}</el-tag>
          <el-tag size="small">{{ file.size_kb }} KB</el-tag>
          <el-button size="small" type="primary" icon="el-icon-download" @click="handleDownload">
            下载
          </el-button>
        </div>
      </div>

      <!-- 预览内容区 -->
      <div class="preview-body">
        <!-- PDF 文件：iframe 内联预览 -->
        <iframe
          v-if="file.ext === '.pdf'"
          :src="previewUrl"
          class="pdf-viewer"
          frameborder="0"
        ></iframe>

        <!-- DOC/DOCX 文件：暂不支持直接预览 -->
        <div v-else-if="file.ext === '.doc' || file.ext === '.docx'" class="unsupported-preview">
          <i class="el-icon-tickets unsupported-icon"></i>
          <h3>{{ file.filename }}</h3>
          <p class="unsupported-hint">Word 文档暂不支持在线预览，请下载后查看</p>
          <div class="file-detail">
            <div class="detail-row">
              <span class="label">文件类型：</span>
              <span>{{ file.ext === '.docx' ? 'Word 文档 (.docx)' : 'Word 97-2003 文档 (.doc)' }}</span>
            </div>
            <div class="detail-row">
              <span class="label">文件大小：</span>
              <span>{{ file.size_kb }} KB</span>
            </div>
            <div class="detail-row">
              <span class="label">所属分类：</span>
              <span>{{ file.category }}</span>
            </div>
          </div>
          <el-button type="primary" icon="el-icon-download" @click="handleDownload">
            下载文件
          </el-button>
        </div>

        <!-- TXT 文件：直接加载文本预览 -->
        <div v-else-if="file.ext === '.txt'" class="txt-preview">
          <div v-if="txtLoading" class="txt-loading" v-loading="true">加载中...</div>
          <pre v-else class="txt-content">{{ txtContent }}</pre>
        </div>

        <!-- 其他文件 -->
        <div v-else class="unsupported-preview">
          <i class="el-icon-question unsupported-icon"></i>
          <p>不支持预览此类型文件</p>
          <el-button type="primary" icon="el-icon-download" @click="handleDownload">
            下载文件
          </el-button>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import apiClient from '@/api'

export default {
  name: 'FilePreview',
  props: {
    file: {
      type: Object,
      default: null
      // { category, subdir, filename, ext, size_kb }
    }
  },
  data() {
    return {
      txtContent: '',
      txtLoading: false
    }
  },
  computed: {
    previewUrl() {
      if (!this.file) return ''
      return apiClient.getKnowledgePreviewUrl(this.file.subdir, this.file.filename)
    },
    downloadUrl() {
      if (!this.file) return ''
      return apiClient.getKnowledgeDownloadUrl(this.file.subdir, this.file.filename)
    }
  },
  watch: {
    file: {
      handler(newFile) {
        if (newFile && newFile.ext === '.txt') {
          this.loadTxtContent()
        }
      },
      immediate: true
    }
  },
  methods: {
    handleDownload() {
      window.open(this.downloadUrl, '_blank')
    },

    async loadTxtContent() {
      this.txtLoading = true
      try {
        const response = await fetch(this.previewUrl)
        this.txtContent = await response.text()
      } catch (e) {
        this.txtContent = '加载失败: ' + e.message
      } finally {
        this.txtLoading = false
      }
    },

    getFileIcon(ext) {
      const icons = {
        '.pdf': 'el-icon-document',
        '.doc': 'el-icon-tickets',
        '.docx': 'el-icon-tickets',
        '.txt': 'el-icon-notebook-2'
      }
      return icons[ext] || 'el-icon-document'
    },

    getExtTagType(ext) {
      const types = {
        '.pdf': 'danger',
        '.doc': 'primary',
        '.docx': 'primary',
        '.txt': ''
      }
      return types[ext] || 'info'
    }
  }
}
</script>

<style scoped>
.file-preview {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: transparent;
}

/* 空状态 */
.empty-preview {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #aaa;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.25;
}

/* 顶部信息栏 */
.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  border-bottom: 1px solid rgba(242, 153, 74, 0.2);
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  flex-shrink: 0;
}

.file-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.file-title i {
  font-size: 18px;
  color: #f2994a;
  flex-shrink: 0;
}

.file-title span {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

/* 下载按钮统一橙色 */
.header-actions >>> .el-button--primary {
  background-color: #f2994a !important;
  border-color: #f2994a !important;
}

.header-actions >>> .el-button--primary:hover {
  background-color: #e8893a !important;
  border-color: #e8893a !important;
}

/* 预览内容区 */
.preview-body {
  flex: 1;
  overflow: hidden;
}

/* PDF 预览 */
.pdf-viewer {
  width: 100%;
  height: 100%;
  border: none;
}

/* 不支持预览的文件 */
.unsupported-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 40px;
  text-align: center;
}

.unsupported-icon {
  font-size: 64px;
  color: rgba(242, 153, 74, 0.3);
  margin-bottom: 16px;
}

.unsupported-preview h3 {
  font-size: 16px;
  color: #303133;
  margin: 0 0 8px 0;
  word-break: break-all;
}

.unsupported-hint {
  color: #909399;
  font-size: 14px;
  margin-bottom: 24px;
}

.file-detail {
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(242, 153, 74, 0.2);
  border-radius: 8px;
  padding: 16px 24px;
  margin-bottom: 24px;
  text-align: left;
  backdrop-filter: blur(6px);
}

.detail-row {
  padding: 6px 0;
  font-size: 14px;
  color: #606266;
}

.detail-row .label {
  color: #909399;
  margin-right: 8px;
}

/* TXT 预览 */
.txt-preview {
  height: 100%;
  overflow: auto;
}

.txt-loading {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.txt-content {
  margin: 0;
  padding: 20px;
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: 'PingFang SC', 'Microsoft YaHei', monospace;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(6px);
}
</style>
