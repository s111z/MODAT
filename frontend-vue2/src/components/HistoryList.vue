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

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

export default {
  name: 'HistoryList',
  data() {
    return {
      searchQuery: '',
      sessions: [
        {
          id: '1',
          title: '深度学习模型优化讨论',
          preview: '讨论了学习率调整、批量大小优化等最佳实践...',
          timestamp: new Date(Date.now() - 1000 * 60 * 30),
          messageCount: 8
        },
        {
          id: '2',
          title: '劳动合同法咨询',
          preview: '关于劳动合同解除的法律问题...',
          timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2),
          messageCount: 12
        },
        {
          id: '3',
          title: 'Python 数据分析',
          preview: '使用 pandas 进行数据清洗和分析...',
          timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24),
          messageCount: 15
        }
      ]
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
    formatTime(timestamp) {
      return dayjs(timestamp).fromNow()
    },
    handleSessionClick(session) {
      this.$message.info(`加载会话: ${session.title}`)
      // TODO: 实现会话加载逻辑
    }
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
