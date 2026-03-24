<template>
  <div class="home">
    <!-- 侧边栏 -->
    <div class="sidebar">
      <div class="sidebar-buttons">
        <!-- 对话图标 -->
        <div
          @click="setSidebar('chat')"
          :class="['sidebar-btn', { active: sidebarActive === 'chat' }]"
        >
          <img src="@/assets/images/side1.png" class="sidebar-icon" alt="chat" />
        </div>

        <!-- 历史会话图标 -->
        <div
          @click="setSidebar('history')"
          :class="['sidebar-btn', { active: sidebarActive === 'history' }]"
        >
          <img src="@/assets/images/side2.png" class="sidebar-icon" alt="chat" />
        </div>

        <!-- 全局搜索图标 -->
        <div
          @click="setSidebar('search')"
          :class="['sidebar-btn', { active: sidebarActive === 'search' }]"
        >
          <img src="@/assets/images/side3.png" class="sidebar-icon" alt="chat" />
        </div>

        <!-- 知识库管理图标 -->
        <div
          @click="setSidebar('knowledge')"
          :class="['sidebar-btn', { active: sidebarActive === 'knowledge' }]"
        >
          <img src="@/assets/images/side4.png" class="sidebar-icon" alt="chat" />
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧面板：根据侧边栏状态显示不同内容 -->
      <div class="left-panel">
        

        <!-- 聊天模式下根据任务模式显示不同内容 -->
        <template v-if="sidebarActive === 'chat'">
          <!-- QA 模式显示 AgentWorkflow（知识问答）或 AgentThinking（普通QA） -->
          <AgentWorkflow
            v-if="taskMode === 'qa' && workflowSteps.length > 0"
            :steps="workflowSteps"
            ref="agentWorkflow"
          />
          <AgentThinking v-else-if="taskMode === 'qa'" />

          <!-- 文档审核模式显示 DocumentReviewPanel -->
          <DocumentReviewPanel v-else />
        </template>

        <!-- 历史列表 -->
        <HistoryList v-else-if="sidebarActive === 'history'" />

        <!-- 全局搜索 -->
        <GlobalSearch v-else-if="sidebarActive === 'search'" />

        <!-- 知识库管理 -->
        <KnowledgeManager v-else-if="sidebarActive === 'knowledge'" />
      </div>

      <!-- 右侧面板：始终显示聊天界面 -->
      <div class="right-panel">
        <ChatInterface />
      </div>
    </div>
  </div>
</template>

<script>
import { mapState, mapMutations } from 'vuex'
import ChatInterface from '@/components/ChatInterface.vue'
import AgentThinking from '@/components/AgentThinking.vue'
import AgentWorkflow from '@/components/AgentWorkflow.vue'
import DocumentReviewPanel from '@/components/DocumentReviewPanel.vue'
import HistoryList from '@/components/HistoryList.vue'
import GlobalSearch from '@/components/GlobalSearch.vue'
import KnowledgeManager from '@/components/KnowledgeManager.vue'

export default {
  name: 'Home',
  components: {
    ChatInterface,
    AgentThinking,
    AgentWorkflow,
    DocumentReviewPanel,
    HistoryList,
    GlobalSearch,
    KnowledgeManager
  },
  data() {
    return {
      workflowSteps: []
    }
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
  width: 100vw;
  /* 引用你的本地图片路径 */
  /* Vite 常用路径写法，如果配置了 alias @，可以使用 @/assets/... */
  background-image: url('@/assets/images/check_background.png');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
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

/* 主内容区 */
.main-content {
  display: flex;
  flex: 1;
  height: 100vh;
  overflow: hidden;
}

/* 左侧面板 */
.left-panel {
  width: 30%;
  height: 100vh;
  border-right: 1px solid #e5e7eb;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(8px);
  overflow-y: auto;
  transition: all 0.3s;
}
.panel-header-tabs {
  display: flex;
  background-color: #e8d5c4; /* 截图中的浅啡色背景 */
  padding: 0 10px;
  height: 48px;
  align-items: center;
}

.tab-item {
  flex: 1;
  text-align: center;
  font-size: 14px;
  color: #5d4037;
  cursor: pointer;
  padding: 10px 0;
  transition: all 0.3s;
}

.tab-item.active {
  font-weight: bold;
  border-bottom: 2px solid #5d4037;
}

.left-panel {
  width: 30%;
  background: transparent; /* 截图左侧主要是纯白底色 */
  border-right: 1px solid #d1d5db;
}

/* 右侧面板 */
.right-panel {
  width: 70%;
  height: 100vh;
  transition: all 0.3s;
  background: transparent;
}

/* 响应式布局 */
@media (max-width: 1024px) {
  .left-panel {
    display: none;
  }

  .right-panel {
    width: 100%;
  }
}
.sidebar-icon {
  width: 24px;
  height: 24px;
  object-fit: contain;
  transition: all 0.2s;
  /* 如果你的图片是黑灰色的，未激活时可以稍微降一点透明度 */
  opacity: 0.6; 
}

/* 当父级按钮处于 active 状态时，图标全亮 */
.sidebar-btn.active .sidebar-icon {
  opacity: 1;
  /* 如果你想让图标在激活时有蓝色阴影或滤镜，可以加这一行 */
  /* filter: drop-shadow(0 0 2px rgba(59, 130, 246, 0.5)); */
}

.sidebar-btn:hover .sidebar-icon {
  opacity: 0.9;
}
</style>
