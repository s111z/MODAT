<template>
  <div class="home-single single-layout">
    <!-- 侧边栏 -->
    <div class="sidebar">
      <div class="sidebar-buttons">
        <!-- 对话图标 -->
        <div
          @click="setSidebar('chat')"
          :class="['sidebar-btn', { active: sidebarActive === 'chat' }]"
        >
          <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
        </div>

        <!-- 历史会话图标 -->
        <div
          @click="setSidebar('history')"
          :class="['sidebar-btn', { active: sidebarActive === 'history' }]"
        >
          <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
          </svg>
        </div>

        <!-- 全局搜索图标 -->
        <div
          @click="setSidebar('search')"
          :class="['sidebar-btn', { active: sidebarActive === 'search' }]"
        >
          <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
        </div>

        <!-- 知识库管理图标 -->
        <div
          @click="setSidebar('knowledge')"
          :class="['sidebar-btn', { active: sidebarActive === 'knowledge' }]"
        >
          <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
          </svg>
        </div>
      </div>
    </div>

    <!-- 主内容区 - 单栏布局 -->
    <div class="main-content-single">
      <!-- 聊天模式 -->
      <div v-if="sidebarActive === 'chat'" class="chat-container">
        <ChatInterface />
      </div>

      <!-- 历史列表 -->
      <div v-else-if="sidebarActive === 'history'" class="panel-container">
        <HistoryList />
      </div>

      <!-- 全局搜索 -->
      <div v-else-if="sidebarActive === 'search'" class="panel-container">
        <GlobalSearch />
      </div>

      <!-- 知识库管理 -->
      <div v-else-if="sidebarActive === 'knowledge'" class="panel-container">
        <KnowledgeManager />
      </div>
    </div>
  </div>
</template>

<script>
import { mapState, mapMutations } from 'vuex'
import ChatInterface from '@/components/ChatInterface.vue'
import HistoryList from '@/components/HistoryList.vue'
import GlobalSearch from '@/components/GlobalSearch.vue'
import KnowledgeManager from '@/components/KnowledgeManager.vue'

export default {
  name: 'HomeSingle',
  components: {
    ChatInterface,
    HistoryList,
    GlobalSearch,
    KnowledgeManager
  },
  computed: {
    ...mapState(['sidebarActive', 'taskMode'])
  },
  methods: {
    ...mapMutations(['SET_SIDEBAR_ACTIVE', 'SET_LAYOUT_MODE']),

    setSidebar(panel) {
      this.SET_SIDEBAR_ACTIVE(panel)
    }
  },
  mounted() {
    // 设置为单栏模式
    this.SET_LAYOUT_MODE('single')
    console.log('HomeSingle component mounted - Single column layout')
  }
}
</script>

<style scoped>
.home-single {
  display: flex;
  height: 100vh;
  background: linear-gradient(to bottom right, #eff6ff, #e0e7ff);
  overflow: hidden;
}

/* 侧边栏 */
.sidebar {
  width: 64px;
  background: white;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 24px;
  flex-shrink: 0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  z-index: 100;
}

.sidebar-buttons {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.sidebar-btn {
  width: 24px;
  height: 24px;
  cursor: pointer;
  transition: all 0.2s;
  color: #9ca3af;
}

.sidebar-btn:hover {
  color: #6b7280;
}

.sidebar-btn.active {
  color: #3b82f6;
}

.sidebar-btn svg {
  width: 100%;
  height: 100%;
}

/* 主内容区 - 单栏 */
.main-content-single {
  flex: 1;
  height: 100vh;
  overflow: hidden;
  display: flex;
}

.chat-container {
  flex: 1;
  height: 100vh;
  display: flex;
  width: 100%;
}

.panel-container {
  flex: 1;
  height: 100vh;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(8px);
  overflow-y: auto;
  width: 100%;
}
</style>
