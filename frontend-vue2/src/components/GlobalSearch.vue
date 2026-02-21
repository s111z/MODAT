<template>
  <div class="global-search">
    <div class="header">
      <h3>🔍 全局搜索</h3>
      <p>搜索所有会话和文档中的内容</p>
    </div>

    <el-input
      v-model="searchQuery"
      placeholder="输入关键词搜索..."
      prefix-icon="el-icon-search"
      size="medium"
      @input="handleSearch"
      class="search-input"
    ></el-input>

    <div v-if="isSearching" class="loading-state">
      <i class="el-icon-loading"></i>
      <p>搜索中...</p>
    </div>

    <div v-else-if="searchQuery.length > 0 && searchQuery.length < 2" class="hint">
      请输入至少 2 个字符进行搜索
    </div>

    <div v-else-if="searchResults.length === 0 && searchQuery.length >= 2" class="empty-state">
      <i class="el-icon-search"></i>
      <p>未找到匹配的结果</p>
    </div>

    <div v-else-if="searchResults.length > 0" class="results-list">
      <div class="results-header">
        找到 {{ searchResults.length }} 个结果
      </div>

      <el-card
        v-for="result in searchResults"
        :key="result.id"
        class="result-card"
        shadow="hover"
      >
        <div class="result-header">
          <h4>{{ result.sessionTitle }}</h4>
          <span class="result-time">{{ formatTime(result.timestamp) }}</span>
        </div>

        <p class="result-content" v-html="highlightMatch(result.matchedContent)"></p>

        <div class="result-context">
          <el-tag size="mini" type="info">{{ result.context }}</el-tag>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script>
import dayjs from 'dayjs'
import mockService from '@/mock'

export default {
  name: 'GlobalSearch',
  data() {
    return {
      searchQuery: '',
      isSearching: false,
      searchResults: [],
      recentSearches: []
    }
  },
  methods: {
    async handleSearch() {
      if (this.searchQuery.length < 2) {
        this.searchResults = []
        return
      }

      this.isSearching = true

      try {
        if (mockService.isEnabled()) {
          // 模拟搜索延迟
          await new Promise(resolve => setTimeout(resolve, 300))

          const results = await mockService.search(this.searchQuery)
          this.searchResults = results.map(result => ({
            id: result.id,
            sessionId: result.id,
            sessionTitle: result.title,
            matchedContent: result.excerpt,
            timestamp: new Date(result.date),
            context: `${result.type} | ${result.source}`
          }))
        } else {
          // 真实 API 调用
          // TODO: 实现真实搜索API
          this.searchResults = []
        }
      } catch (error) {
        console.error('搜索失败:', error)
        this.searchResults = []
      } finally {
        this.isSearching = false
      }
    },

    highlightMatch(content) {
      if (!this.searchQuery) return content
      const regex = new RegExp(`(${this.searchQuery})`, 'gi')
      return content.replace(regex, '<mark>$1</mark>')
    },

    formatTime(timestamp) {
      return dayjs(timestamp).format('YYYY-MM-DD HH:mm')
    },

    loadRecentSearches() {
      if (mockService.isEnabled()) {
        const searchData = mockService.getGlobalSearchData()
        this.recentSearches = searchData.recentSearches || []
      }
    }
  },
  mounted() {
    this.loadRecentSearches()
  }
}
</script>

<style scoped>
.global-search {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 20px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}

.header {
  margin-bottom: 16px;
}

.header h3 {
  font-size: 18px;
  font-weight: 600;
  margin: 0 0 4px 0;
}

.header p {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

.search-input {
  margin-bottom: 16px;
}

.loading-state,
.empty-state,
.hint {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
}

.loading-state i,
.empty-state i {
  font-size: 48px;
  margin-bottom: 12px;
}

.hint {
  font-size: 14px;
}

.results-list {
  flex: 1;
  overflow-y: auto;
}

.results-header {
  font-size: 14px;
  color: #6b7280;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: #f9fafb;
  border-radius: 4px;
}

.result-card {
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.result-card:hover {
  transform: translateX(4px);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.result-header h4 {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin: 0;
}

.result-time {
  font-size: 12px;
  color: #9ca3af;
}

.result-content {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.6;
  margin: 8px 0;
}

.result-content >>> mark {
  background: #fef3c7;
  color: #92400e;
  padding: 2px 4px;
  border-radius: 2px;
  font-weight: 500;
}

.result-context {
  margin-top: 8px;
}
</style>
