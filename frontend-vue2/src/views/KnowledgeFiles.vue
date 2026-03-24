<template>
  <div class="knowledge-files-page">
    <div class="page-header">
      <h1>知识库文件浏览</h1>
      <el-button size="small" icon="el-icon-refresh" @click="loadFileTree" :loading="loading">
        刷新
      </el-button>
    </div>

    <div class="page-content" v-loading="loading">
      <div v-if="!loading && Object.keys(tree).length === 0" class="empty-state">
        <i class="el-icon-folder-opened empty-icon"></i>
        <p>知识库目录为空</p>
      </div>

      <div v-else class="file-tree">
        <div v-for="(files, category) in tree" :key="category" class="category-group">
          <div class="category-header" @click="toggleCategory(category)">
            <i :class="expanded[category] ? 'el-icon-arrow-down' : 'el-icon-arrow-right'"></i>
            <i class="el-icon-folder category-icon"></i>
            <span class="category-name">{{ category }}</span>
            <el-tag size="mini" type="info">{{ files.length }} 个文件</el-tag>
          </div>

          <transition name="slide">
            <div v-show="expanded[category]" class="category-files">
              <div v-for="file in files" :key="file.filename" class="file-row">
                <div class="file-info">
                  <i class="el-icon-document file-icon"></i>
                  <span class="file-name">{{ file.filename }}</span>
                </div>
                <div class="file-meta">
                  <el-tag size="mini">{{ file.size_kb }} KB</el-tag>
                  <el-tag size="mini" :type="file.ext === '.pdf' ? 'danger' : 'primary'">{{ file.ext }}</el-tag>
                  <el-button type="text" size="mini" icon="el-icon-download" @click="download(category, file.filename)">
                    下载
                  </el-button>
                </div>
              </div>
            </div>
          </transition>
        </div>
      </div>
    </div>

    <div class="page-footer">
      共 {{ totalCount }} 个文件，{{ Object.keys(tree).length }} 个分类
    </div>
  </div>
</template>

<script>
import apiClient from '@/api'

export default {
  name: 'KnowledgeFiles',
  data() {
    return {
      tree: {},
      loading: true,
      expanded: {}
    }
  },
  computed: {
    totalCount() {
      let n = 0
      Object.values(this.tree).forEach(f => { n += f.length })
      return n
    }
  },
  async created() {
    await this.loadFileTree()
  },
  methods: {
    async loadFileTree() {
      this.loading = true
      try {
        const res = await apiClient.getKnowledgeTree()
        this.tree = res.tree
        Object.keys(this.tree).forEach(k => {
          this.$set(this.expanded, k, true)
        })
      } catch (e) {
        this.$message.error(e.message)
      } finally {
        this.loading = false
      }
    },
    toggleCategory(cat) {
      this.$set(this.expanded, cat, !this.expanded[cat])
    },
    download(category, filename) {
      const subdir = category === '根目录' ? '.' : category
      const url = apiClient.getKnowledgeDownloadUrl(subdir, filename)
      window.open(url, '_blank')
    }
  }
}
</script>

<style scoped>
.knowledge-files-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.page-content {
  flex: 1;
  overflow-y: auto;
}

.empty-state {
  text-align: center;
  padding: 60px 0;
  color: #c0c4cc;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 12px;
}

.file-tree {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.category-group {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  overflow: hidden;
}

.category-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f5f7fa;
  cursor: pointer;
  user-select: none;
}

.category-header:hover {
  background: #ebeef5;
}

.category-icon {
  color: #e6a23c;
}

.category-name {
  flex: 1;
  font-weight: 600;
  color: #303133;
}

.category-files {
  border-top: 1px solid #ebeef5;
}

.file-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px 10px 40px;
  border-bottom: 1px solid #f2f3f5;
}

.file-row:last-child {
  border-bottom: none;
}

.file-row:hover {
  background: #fafafa;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.file-icon {
  color: #909399;
}

.file-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  color: #303133;
}

.file-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: all 0.25s ease;
  max-height: 1000px;
  overflow: hidden;
}

.slide-enter,
.slide-leave-to {
  max-height: 0;
  opacity: 0;
}

.page-footer {
  padding: 12px 0;
  text-align: center;
  color: #909399;
  font-size: 14px;
  border-top: 1px solid #ebeef5;
  margin-top: 16px;
}
</style>
