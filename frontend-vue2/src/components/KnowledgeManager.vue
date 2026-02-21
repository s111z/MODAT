<template>
  <div class="knowledge-manager">
    <!-- 标题栏 -->
    <div class="header">
      <h2>知识库管理</h2>
      <p>管理向量数据库中的文档，支持上传、搜索和删除</p>
    </div>

    <!-- 上传区域 -->
    <div class="upload-section">
      <input
        ref="fileInput"
        type="file"
        style="display: none"
        accept=".pdf"
        @change="handleFileUpload"
        :disabled="isUploading"
      />

      <el-button
        type="primary"
        @click="$refs.fileInput.click()"
        :loading="isUploading"
        :disabled="isUploading"
        class="upload-btn"
      >
        <i v-if="!isUploading" class="el-icon-upload el-icon--left"></i>
        {{ isUploading ? '处理中...' : '上传PDF到知识库' }}
      </el-button>

      <!-- 上传状态显示 -->
      <el-alert
        v-if="uploadStatus.type"
        :type="uploadStatus.type === 'success' ? 'success' : 'error'"
        :title="uploadStatus.message"
        :closable="true"
        @close="uploadStatus.type = ''"
        class="upload-status"
      >
        <div v-if="processingSteps.length > 0" class="processing-steps">
          <p v-for="(step, index) in processingSteps" :key="index" class="step-text">
            • {{ step }}
          </p>
        </div>
      </el-alert>
    </div>

    <!-- 搜索区域 -->
    <div class="search-section">
      <div class="search-bar">
        <el-input
          v-model="searchQuery"
          placeholder="搜索知识库内容..."
          :disabled="isSearching"
          @keyup.enter.native="handleSearch"
          class="search-input"
        >
          <el-button
            slot="append"
            icon="el-icon-search"
            @click="handleSearch"
            :loading="isSearching"
          ></el-button>
        </el-input>

        <el-button
          icon="el-icon-refresh"
          @click="loadDocuments"
          :loading="isLoading"
          title="刷新列表"
          class="refresh-btn"
        ></el-button>
      </div>

      <div v-if="searchResults.length > 0" class="search-info">
        找到 {{ searchResults.length }} 个相关结果
        <el-button
          type="text"
          size="mini"
          @click="clearSearch"
          class="clear-btn"
        >
          清除搜索
        </el-button>
      </div>
    </div>

    <!-- 文档列表 -->
    <div class="documents-section" v-loading="isLoading">
      <div v-if="!isLoading && displayedDocuments.length === 0" class="empty-state">
        <i class="el-icon-document empty-icon"></i>
        <p>{{ searchQuery ? '未找到匹配的文档' : '知识库为空，请上传文档' }}</p>
      </div>

      <div v-else class="documents-list">
        <el-card
          v-for="doc in displayedDocuments"
          :key="doc.id"
          class="document-card"
          shadow="hover"
        >
          <div slot="header" class="card-header">
            <div class="header-left">
              <i class="el-icon-document document-icon"></i>
              <span class="document-title">
                {{ doc.metadata && doc.metadata.source ? doc.metadata.source : doc.id }}
              </span>
            </div>
            <el-button
              type="danger"
              icon="el-icon-delete"
              size="mini"
              circle
              @click="handleDelete(doc.id)"
              class="delete-btn"
            ></el-button>
          </div>

          <div class="card-content">
            <p class="document-content">{{ doc.content }}</p>
            <div class="metadata-tags">
              <el-tag
                v-if="doc.metadata && doc.metadata.category"
                size="mini"
                type="info"
              >
                {{ doc.metadata.category }}
              </el-tag>
              <el-tag
                v-if="doc.metadata && doc.metadata.chunk_index !== undefined"
                size="mini"
              >
                Chunk {{ doc.metadata.chunk_index + 1 }}/{{ doc.metadata.total_chunks }}
              </el-tag>
              <el-tag
                v-if="doc.metadata && doc.metadata.file_type"
                size="mini"
                type="success"
              >
                {{ doc.metadata.file_type }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 底部统计 -->
    <div class="footer">
      共 {{ documents.length }} 个文档块
    </div>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'
import mockService from '@/mock'

export default {
  name: 'KnowledgeManager',
  data() {
    return {
      searchQuery: '',
      isUploading: false,
      uploadStatus: {
        type: '',
        message: ''
      },
      processingSteps: []
    }
  },
  computed: {
    ...mapState('knowledge', ['documents', 'isLoading', 'searchResults', 'isSearching']),
    displayedDocuments() {
      return this.searchResults.length > 0 ? this.searchResults : this.documents
    }
  },
  methods: {
    ...mapActions('knowledge', ['fetchDocuments', 'searchDocuments', 'deleteDocument']),

    async loadDocuments() {
      if (mockService.isEnabled()) {
        // 从 Mock 服务加载文档
        try {
          const knowledgeData = mockService.getKnowledgeData()
          // 转换文档格式
          const mockDocuments = knowledgeData.documents.map(doc => ({
            id: doc.id,
            content: `${doc.title} - ${doc.category}`,
            metadata: {
              source: doc.title,
              category: doc.category,
              file_type: doc.format,
              size: doc.size,
              uploadBy: doc.uploadBy,
              uploadDate: doc.uploadDate,
              status: doc.status,
              tags: doc.tags.join(', ')
            }
          }))

          this.$store.commit('knowledge/SET_DOCUMENTS', mockDocuments)
          this.$store.commit('knowledge/SET_LOADING', false)
        } catch (error) {
          this.$message.error('加载文档列表失败: ' + error.message)
        }
      } else {
        // 真实 API
        try {
          await this.fetchDocuments(50)
        } catch (error) {
          this.$message.error('加载文档列表失败: ' + error.message)
        }
      }
    },

    async handleFileUpload(e) {
      const files = e.target.files
      if (!files || files.length === 0) return

      const file = files[0]
      this.isUploading = true
      this.uploadStatus = { type: '', message: '' }
      this.processingSteps = []

      try {
        if (mockService.isEnabled()) {
          // Mock 模式
          this.processingSteps.push('正在上传文件...')
          await new Promise(resolve => setTimeout(resolve, 500))

          this.processingSteps.push('正在解析文档结构...')
          await new Promise(resolve => setTimeout(resolve, 500))

          this.processingSteps.push('正在添加到知识库...')
          const result = await mockService.uploadDocument(file, {
            category: '技术文档',
            tags: ['新上传']
          })

          this.uploadStatus = {
            type: 'success',
            message: '文件已成功添加到知识库（Mock）'
          }

          // 刷新列表
          await this.loadDocuments()
        } else {
          // 真实 API
          this.processingSteps.push('正在上传文件...')
          const uploadResponse = await this.$store.dispatch('knowledge/uploadAndAddDocument', {
            file,
            metadatas: {
              category: 'law',
              permissions: 0
            }
          })

          this.uploadStatus = {
            type: 'success',
            message: `${uploadResponse.message} - 文件已成功添加到知识库`
          }

          if (uploadResponse.steps && uploadResponse.steps.length > 0) {
            this.processingSteps.push(...uploadResponse.steps)
          }
        }
      } catch (error) {
        this.uploadStatus = {
          type: 'error',
          message: error.message || '处理失败'
        }
      } finally {
        this.isUploading = false
        // 清空文件输入
        if (this.$refs.fileInput) {
          this.$refs.fileInput.value = ''
        }
      }
    },

    async handleSearch() {
      if (!this.searchQuery.trim()) {
        this.$store.commit('knowledge/SET_SEARCH_RESULTS', [])
        return
      }

      if (mockService.isEnabled()) {
        // Mock 搜索
        try {
          this.$store.commit('knowledge/SET_SEARCHING', true)
          const results = await mockService.search(this.searchQuery)

          // 转换搜索结果
          const searchResults = results.map(result => ({
            id: result.id,
            content: result.excerpt,
            metadata: {
              source: result.title,
              category: result.type,
              relevance: result.relevance
            }
          }))

          this.$store.commit('knowledge/SET_SEARCH_RESULTS', searchResults)
          this.$store.commit('knowledge/SET_SEARCHING', false)
          this.$message.success(`找到 ${searchResults.length} 个相关结果`)
        } catch (error) {
          this.$store.commit('knowledge/SET_SEARCHING', false)
          this.$message.error('搜索失败: ' + error.message)
        }
      } else {
        // 真实 API
        try {
          await this.searchDocuments(this.searchQuery)
          this.$message.success(`找到 ${this.searchResults.length} 个相关结果`)
        } catch (error) {
          this.$message.error('搜索失败: ' + error.message)
        }
      }
    },

    async handleDelete(docId) {
      try {
        await this.$confirm('确定要删除这个文档吗？', '警告', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })

        if (mockService.isEnabled()) {
          // Mock 删除
          await mockService.deleteDocument(docId)
          this.$message.success('删除成功（Mock）')
          // 刷新列表
          await this.loadDocuments()
        } else {
          // 真实 API
          await this.deleteDocument(docId)
          this.$message.success('删除成功')
        }
      } catch (error) {
        if (error !== 'cancel') {
          this.$message.error('删除失败: ' + error.message)
        }
      }
    },

    clearSearch() {
      this.searchQuery = ''
      this.$store.commit('knowledge/SET_SEARCH_RESULTS', [])
    }
  },
  mounted() {
    this.loadDocuments()
  }
}
</script>

<style scoped>
.knowledge-manager {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
}

/* 标题栏 */
.header {
  padding: 16px 24px;
  border-bottom: 1px solid #e0e0e0;
  background: #f9fafb;
}

.header h2 {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0 0 4px 0;
}

.header p {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

/* 上传区域 */
.upload-section {
  padding: 16px 24px;
  border-bottom: 1px solid #e0e0e0;
}

.upload-btn {
  width: 100%;
}

.upload-status {
  margin-top: 12px;
}

.processing-steps {
  margin-top: 8px;
}

.step-text {
  font-size: 12px;
  opacity: 0.75;
  margin: 4px 0;
}

/* 搜索区域 */
.search-section {
  padding: 16px 24px;
  border-bottom: 1px solid #e0e0e0;
}

.search-bar {
  display: flex;
  gap: 8px;
}

.search-input {
  flex: 1;
}

.search-info {
  margin-top: 8px;
  font-size: 14px;
  color: #6b7280;
}

.clear-btn {
  margin-left: 8px;
}

/* 文档列表 */
.documents-section {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #9ca3af;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.3;
}

.documents-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.document-card {
  transition: all 0.3s;
}

.document-card:hover {
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.document-icon {
  color: #3b82f6;
  font-size: 16px;
}

.document-title {
  font-size: 14px;
  font-weight: 500;
  color: #111827;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.delete-btn {
  flex-shrink: 0;
}

.card-content {
  padding-top: 0;
}

.document-content {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.5;
  margin: 0 0 8px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.metadata-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

/* 底部统计 */
.footer {
  padding: 12px 24px;
  border-top: 1px solid #e0e0e0;
  background: #f9fafb;
  font-size: 14px;
  color: #6b7280;
  text-align: center;
}
</style>
