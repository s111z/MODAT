<template>
  <div class="knowledge-manager">
    <!-- 标题栏 -->
    <div class="header">
      <h2>知识库管理</h2>
      <p>管理向量数据库中的文档，支持上传、搜索和删除</p>
    </div>

    <!-- Tab 切换 -->
    <div class="tab-bar">
      <div
        :class="['tab-item', { active: activeTab === 'vectordb' }]"
        @click="activeTab = 'vectordb'"
      >
        向量库文档
      </div>
      <div
        :class="['tab-item', { active: activeTab === 'files' }]"
        @click="switchToFiles"
      >
        知识库源文件
      </div>
    </div>

    <!-- ===== Tab 1: 向量库文档（原有功能） ===== -->
    <template v-if="activeTab === 'vectordb'">
      <!-- 上传与同步区域 -->
      <div class="upload-section">
        <div class="action-row">
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
            :disabled="isUploading || isSyncing"
            size="small"
          >
            <i v-if="!isUploading" class="el-icon-upload el-icon--left"></i>
            {{ isUploading ? '处理中...' : '上传PDF' }}
          </el-button>

          <el-button
            type="success"
            @click="handleSync"
            :loading="isSyncing"
            :disabled="isSyncing || isUploading"
            size="small"
          >
            <i v-if="!isSyncing" class="el-icon-refresh el-icon--left"></i>
            {{ isSyncing ? '同步中...' : '同步知识库' }}
          </el-button>
        </div>

        <!-- 同步结果显示 -->
        <el-alert
          v-if="syncResult.type"
          :type="syncResult.type"
          :title="syncResult.message"
          :closable="true"
          @close="syncResult.type = ''"
          class="upload-status"
          show-icon
        >
          <div v-if="syncResult.details" class="sync-details">
            <span v-if="syncResult.details.added > 0" class="sync-stat added">新增 {{ syncResult.details.added }}</span>
            <span v-if="syncResult.details.skipped > 0" class="sync-stat skipped">跳过 {{ syncResult.details.skipped }}</span>
            <span v-if="syncResult.details.deleted > 0" class="sync-stat deleted">清理 {{ syncResult.details.deleted }}</span>
            <span v-if="syncResult.details.failed > 0" class="sync-stat failed">失败 {{ syncResult.details.failed }}</span>
          </div>
        </el-alert>

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
    </template>

    <!-- ===== Tab 2: 知识库源文件浏览（左侧选择） ===== -->
    <template v-if="activeTab === 'files'">
      <div class="files-section" v-loading="filesLoading">
        <div v-if="!filesLoading && Object.keys(fileTree).length === 0" class="empty-state">
          <i class="el-icon-folder empty-icon"></i>
          <p>知识库目录为空</p>
        </div>

        <div v-else class="file-tree">
          <div
            v-for="(files, category) in fileTree"
            :key="category"
            class="category-group"
          >
            <div class="category-header" @click="toggleCategory(category)">
              <i :class="expandedCategories[category] ? 'el-icon-arrow-down' : 'el-icon-arrow-right'"></i>
              <i class="el-icon-folder category-icon"></i>
              <span class="category-name">{{ category }}</span>
              <el-tag size="mini" type="info" class="file-count">{{ files.length }}</el-tag>
            </div>

            <transition name="slide">
              <div v-show="expandedCategories[category]" class="category-files">
                <div
                  v-for="file in files"
                  :key="file.filename"
                  :class="['file-row', { selected: isFileSelected(category, file.filename) }]"
                  @click="selectFile(category, file)"
                >
                  <div class="file-info">
                    <i :class="getFileIcon(file.ext)" class="file-type-icon"></i>
                    <span class="file-name" :title="file.filename">{{ file.filename }}</span>
                  </div>
                  <div class="file-meta-inline">
                    <span class="file-size-text">{{ file.size_kb }}KB</span>
                    <el-tag size="mini" :type="getExtTagType(file.ext)" class="ext-tag">{{ file.ext }}</el-tag>
                  </div>
                </div>
              </div>
            </transition>
          </div>
        </div>
      </div>

      <!-- 底部统计 -->
      <div class="footer">
        共 {{ totalFileCount }} 个源文件，{{ Object.keys(fileTree).length }} 个分类
      </div>
    </template>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'
import mockService from '@/mock'
import apiClient from '@/api'

export default {
  name: 'KnowledgeManager',
  data() {
    return {
      activeTab: 'vectordb',
      searchQuery: '',
      isUploading: false,
      uploadStatus: {
        type: '',
        message: ''
      },
      processingSteps: [],
      // 同步相关
      isSyncing: false,
      syncResult: {
        type: '',
        message: '',
        details: null
      },
      // 源文件浏览相关
      fileTree: {},
      filesLoading: false,
      expandedCategories: {},
      selectedFile: null // { category, filename, ext, size_kb }
    }
  },
  computed: {
    ...mapState('knowledge', ['documents', 'isLoading', 'searchResults', 'isSearching']),
    displayedDocuments() {
      return this.searchResults.length > 0 ? this.searchResults : this.documents
    },
    totalFileCount() {
      let count = 0
      Object.values(this.fileTree).forEach(files => {
        count += files.length
      })
      return count
    }
  },
  methods: {
    ...mapActions('knowledge', ['fetchDocuments', 'searchDocuments', 'deleteDocument']),

    // ===== 源文件浏览方法 =====

    async switchToFiles() {
      this.activeTab = 'files'
      if (Object.keys(this.fileTree).length === 0) {
        await this.loadFileTree()
      }
    },

    async loadFileTree() {
      if (mockService.isEnabled()) {
        this.fileTree = {}
        return
      }
      this.filesLoading = true
      try {
        const res = await apiClient.getKnowledgeTree()
        this.fileTree = res.tree
        Object.keys(this.fileTree).forEach(k => {
          this.$set(this.expandedCategories, k, true)
        })
      } catch (e) {
        this.$message.error('加载知识库文件失败: ' + e.message)
      } finally {
        this.filesLoading = false
      }
    },

    toggleCategory(category) {
      this.$set(this.expandedCategories, category, !this.expandedCategories[category])
    },

    selectFile(category, file) {
      this.selectedFile = { category, ...file }
      // 通知 Home.vue 展示预览
      this.$emit('file-selected', {
        category,
        filename: file.filename,
        ext: file.ext,
        size_kb: file.size_kb,
        subdir: category === '根目录' ? '.' : category
      })
    },

    isFileSelected(category, filename) {
      return this.selectedFile &&
        this.selectedFile.category === category &&
        this.selectedFile.filename === filename
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
    },

    // ===== 原有方法 =====

    async handleSync() {
      this.isSyncing = true
      this.syncResult = { type: '', message: '', details: null }

      try {
        const res = await apiClient.syncKnowledge({ category: 'law', permissions: 0 })
        this.syncResult = {
          type: res.failed > 0 ? 'warning' : 'success',
          message: res.message,
          details: {
            added: res.added,
            skipped: res.skipped,
            deleted: res.deleted,
            failed: res.failed
          }
        }
        // 同步完成后刷新向量库文档列表
        await this.loadDocuments()
      } catch (e) {
        this.syncResult = {
          type: 'error',
          message: e.message,
          details: null
        }
      } finally {
        this.isSyncing = false
      }
    },

    async loadDocuments() {
      if (mockService.isEnabled()) {
        try {
          const knowledgeData = mockService.getKnowledgeData()
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
          this.processingSteps.push('正在上传文件...')
          await new Promise(resolve => setTimeout(resolve, 500))

          this.processingSteps.push('正在解析文档结构...')
          await new Promise(resolve => setTimeout(resolve, 500))

          this.processingSteps.push('正在添加到知识库...')
          await mockService.uploadDocument(file, {
            category: '技术文档',
            tags: ['新上传']
          })

          this.uploadStatus = {
            type: 'success',
            message: '文件已成功添加到知识库（Mock）'
          }

          await this.loadDocuments()
        } else {
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
        try {
          this.$store.commit('knowledge/SET_SEARCHING', true)
          const results = await mockService.search(this.searchQuery)

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
          await mockService.deleteDocument(docId)
          this.$message.success('删除成功（Mock）')
          await this.loadDocuments()
        } else {
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
  background: transparent;
}

/* 标题栏 */
.header {
  padding: 16px 24px;
  border-bottom: 1px solid rgba(242, 153, 74, 0.2);
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
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

/* Tab 切换栏 */
.tab-bar {
  display: flex;
  border-bottom: 1px solid rgba(242, 153, 74, 0.2);
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(8px);
}

.tab-item {
  flex: 1;
  text-align: center;
  padding: 12px 0;
  font-size: 14px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 2px solid transparent;
}

.tab-item:hover {
  color: #f2994a;
}

.tab-item.active {
  color: #f2994a;
  font-weight: 600;
  border-bottom-color: #f2994a;
}

/* 上传与同步区域 */
.upload-section {
  padding: 16px 24px;
  border-bottom: 1px solid rgba(242, 153, 74, 0.15);
}

.action-row {
  display: flex;
  gap: 8px;
}

.upload-btn {
  flex: 1;
}

.upload-status {
  margin-top: 12px;
}

.sync-details {
  display: flex;
  gap: 12px;
  margin-top: 4px;
}

.sync-stat {
  font-size: 13px;
  font-weight: 600;
}

.sync-stat.added { color: #67c23a; }
.sync-stat.skipped { color: #909399; }
.sync-stat.deleted { color: #e6a23c; }
.sync-stat.failed { color: #f56c6c; }

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
  border-bottom: 1px solid rgba(242, 153, 74, 0.15);
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
  height: 200px;
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
  background: rgba(255, 255, 255, 0.7) !important;
  backdrop-filter: blur(6px);
  border: 1px solid rgba(242, 153, 74, 0.15) !important;
}

.document-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(242, 153, 74, 0.15) !important;
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
  color: #f2994a;
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

/* ===== 源文件浏览样式 ===== */
.files-section {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
}

.file-tree {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.category-group {
  border: 1px solid rgba(242, 153, 74, 0.2);
  border-radius: 6px;
  overflow: hidden;
}

.category-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.category-header:hover {
  background: rgba(242, 153, 74, 0.08);
}

.category-icon {
  color: #e6a23c;
  font-size: 16px;
}

.category-name {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-count {
  flex-shrink: 0;
}

.category-files {
  border-top: 1px solid rgba(242, 153, 74, 0.15);
}

.file-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px 8px 32px;
  border-bottom: 1px solid rgba(242, 153, 74, 0.08);
  cursor: pointer;
  transition: background 0.15s;
}

.file-row:last-child {
  border-bottom: none;
}

.file-row:hover {
  background: rgba(242, 153, 74, 0.08);
}

.file-row.selected {
  background: rgba(242, 153, 74, 0.15);
  border-left: 3px solid #f2994a;
  padding-left: 29px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.file-type-icon {
  color: #909399;
  font-size: 14px;
  flex-shrink: 0;
}

.file-name {
  font-size: 13px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-meta-inline {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.file-size-text {
  font-size: 11px;
  color: #909399;
}

.ext-tag {
  transform: scale(0.85);
}

/* 展开/收起动画 */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.25s ease;
  max-height: 2000px;
  overflow: hidden;
}

.slide-enter,
.slide-leave-to {
  max-height: 0;
  opacity: 0;
}

/* 底部统计 */
.footer {
  padding: 12px 24px;
  border-top: 1px solid rgba(242, 153, 74, 0.2);
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(8px);
  font-size: 14px;
  color: #6b7280;
  text-align: center;
}
</style>
