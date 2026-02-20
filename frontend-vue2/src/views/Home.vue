<template>
  <div class="home">
    <!-- 侧边栏 -->
    <div class="sidebar">
      <div class="sidebar-buttons">
        <el-tooltip content="聊天" placement="right">
          <el-button
            :type="sidebarActive === 'chat' ? 'primary' : ''"
            circle
            size="medium"
            @click="setSidebar('chat')"
            class="sidebar-btn"
          >
            💬
          </el-button>
        </el-tooltip>

        <el-tooltip content="历史" placement="right">
          <el-button
            :type="sidebarActive === 'history' ? 'primary' : ''"
            circle
            size="medium"
            @click="setSidebar('history')"
            class="sidebar-btn"
          >
            📜
          </el-button>
        </el-tooltip>

        <el-tooltip content="搜索" placement="right">
          <el-button
            :type="sidebarActive === 'search' ? 'primary' : ''"
            circle
            size="medium"
            @click="setSidebar('search')"
            class="sidebar-btn"
          >
            🔍
          </el-button>
        </el-tooltip>

        <el-tooltip content="知识库" placement="right">
          <el-button
            :type="sidebarActive === 'knowledge' ? 'primary' : ''"
            circle
            size="medium"
            @click="setSidebar('knowledge')"
            class="sidebar-btn"
          >
            📚
          </el-button>
        </el-tooltip>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧面板 -->
      <div class="left-panel">
        <!-- QA 模式显示 AgentThinking -->
        <AgentThinking v-if="taskMode === 'qa'" />

        <!-- 文档审核模式显示 DocumentReviewPanel -->
        <DocumentReviewPanel v-else />
      </div>

      <!-- 右侧面板 -->
      <div class="right-panel">
        <!-- 聊天界面 -->
        <ChatInterface v-if="sidebarActive === 'chat'" />

        <!-- 历史列表 -->
        <HistoryList v-else-if="sidebarActive === 'history'" />

        <!-- 全局搜索 -->
        <GlobalSearch v-else-if="sidebarActive === 'search'" />

        <!-- 知识库管理 -->
        <KnowledgeManager v-else-if="sidebarActive === 'knowledge'" />
      </div>
    </div>
  </div>
</template>

<script>
import { mapState, mapMutations } from 'vuex'
import ChatInterface from '@/components/ChatInterface.vue'
import AgentThinking from '@/components/AgentThinking.vue'
import DocumentReviewPanel from '@/components/DocumentReviewPanel.vue'
import HistoryList from '@/components/HistoryList.vue'
import GlobalSearch from '@/components/GlobalSearch.vue'
import KnowledgeManager from '@/components/KnowledgeManager.vue'

export default {
  name: 'Home',
  components: {
    ChatInterface,
    AgentThinking,
    DocumentReviewPanel,
    HistoryList,
    GlobalSearch,
    KnowledgeManager
  },
  computed: {
    ...mapState(['sidebarActive', 'taskMode', 'reviewPhase'])
  },
  methods: {
    ...mapMutations(['SET_SIDEBAR_ACTIVE']),

    setSidebar(panel) {
      this.SET_SIDEBAR_ACTIVE(panel)
    }
  },
  mounted() {
    console.log('Home component mounted successfully')
    console.log('Current mode:', this.taskMode)
    console.log('Current sidebar:', this.sidebarActive)
  }
}
</script>

<style scoped>
.home {
  display: flex;
  height: 100vh;
  background-color: #f5f7fa;
}

/* 侧边栏 */
.sidebar {
  width: 70px;
  background: #2c3e50;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  z-index: 100;
}

.sidebar-buttons {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.sidebar-btn {
  width: 50px;
  height: 50px;
  font-size: 20px;
  transition: all 0.3s;
}

.sidebar-btn:hover {
  transform: scale(1.1);
}

/* 主内容区 */
.main-content {
  display: flex;
  flex: 1;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
}

/* 左侧面板 */
.left-panel {
  width: 45%;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 右侧面板 */
.right-panel {
  width: 55%;
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* 响应式布局 */
@media (max-width: 1024px) {
  .main-content {
    flex-direction: column;
  }

  .left-panel,
  .right-panel {
    width: 100%;
    height: 50%;
  }
}

@media (max-width: 768px) {
  .sidebar {
    width: 60px;
    padding: 15px 0;
  }

  .sidebar-btn {
    width: 44px;
    height: 44px;
    font-size: 18px;
  }

  .left-panel {
    display: none;
  }

  .right-panel {
    width: 100%;
    height: 100%;
  }
}
</style>
