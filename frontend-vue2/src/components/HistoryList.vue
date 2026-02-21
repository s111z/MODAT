<template>
  <div class="history-list">
    <div class="header">
      <h3>📜 历史会话</h3>
      <el-input
        v-model="searchQuery"
        placeholder="搜索历史..."
        prefix-icon="el-icon-search"
        size="small"
        class="search-input"
      ></el-input>
    </div>

    <div class="sessions-list">
      <el-card
        v-for="session in filteredSessions"
        :key="session.id"
        class="session-card"
        shadow="hover"
        @click.native="handleSessionClick(session)"
      >
        <div class="session-header">
          <h4>{{ session.title }}</h4>
          <span class="session-time">{{ formatTime(session.timestamp) }}</span>
        </div>
        <p class="session-preview">{{ session.preview }}</p>
        <div class="session-meta">
          <el-tag size="mini">{{ session.messageCount }} 条消息</el-tag>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script>
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'
import mockService from '@/mock'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

export default {
  name: 'HistoryList',
  data() {
    return {
      searchQuery: '',
      sessions: []
    }
  },
  computed: {
    filteredSessions() {
      if (!this.searchQuery.trim()) {
        return this.sessions
      }
      const query = this.searchQuery.toLowerCase()
      return this.sessions.filter(session =>
        session.title.toLowerCase().includes(query) ||
        session.preview.toLowerCase().includes(query)
      )
    }
  },
  methods: {
    formatTime(dateString) {
      // 如果是日期字符串，解析为相对时间
      const date = new Date(dateString)
      return dayjs(date).fromNow()
    },
    handleSessionClick(session) {
      this.$message.info(`加载会话: ${session.title}`)
      // TODO: 实现会话加载逻辑
    },
    loadSessions() {
      if (mockService.isEnabled()) {
        // 从 Mock 服务加载历史会话
        const mockHistory = mockService.getHistory()
        this.sessions = mockHistory.map(item => ({
          id: item.id,
          title: item.title,
          preview: item.preview,
          timestamp: `${item.date} ${item.time}`,
          messageCount: item.messageCount
        }))
      } else {
        // 真实 API 调用
        // TODO: 实现真实 API
        this.sessions = []
      }
    }
  },
  mounted() {
    this.loadSessions()
  }
}
</script>

<style scoped>
.history-list {
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
  margin: 0 0 12px 0;
}

.search-input {
  width: 100%;
}

.sessions-list {
  flex: 1;
  overflow-y: auto;
}

.session-card {
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.session-card:hover {
  transform: translateX(4px);
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.session-header h4 {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin: 0;
}

.session-time {
  font-size: 12px;
  color: #9ca3af;
}

.session-preview {
  font-size: 13px;
  color: #6b7280;
  margin: 8px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-meta {
  margin-top: 8px;
}
</style>
