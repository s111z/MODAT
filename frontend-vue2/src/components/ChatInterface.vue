<template>
  <div class="chat-interface">
    <div class="right-header">
      <div class="agent-info">
        <div class="agent-avatar"></div>
        <div class="agent-text">
          <div class="agent-name">Compliance Copilot</div>
          <div class="agent-status">Ready</div>
        </div>
      </div>
      
      <div class="header-logo">
        <span class="logo-text">mota</span>
        <img src="@/assets/images/logo.png" alt="Mota" class="logo-icon" />
      </div>
    </div>
    
    <div class="messages-container">
      <div class="messages-list">
        <div v-for="message in messages" :key="message.id" class="message-item">
          <div v-if="message.role === 'user'" class="message user-message">
            <div class="message-bubble user-bubble">
              <p class="message-text">{{ message.content }}</p>
            </div>
          </div>

          <div v-else class="message assistant-message">
            <div class="message-bubble assistant-bubble">
              <AgentWorkflowInline
                v-if="message.workflow && message.workflow.length > 0"
                :steps="message.workflow"
                class="message-workflow"
              />
              <div 
                v-if="message.content" 
                class="message-text markdown-body" 
                v-html="renderMarkdown(message.content)"
              ></div>
            </div>
          </div>
        </div>

        <div v-if="isLoading" class="message assistant-message">
          <div class="message-bubble assistant-bubble loading-bubble">
            <div class="loading-container">
              <div class="dots">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </div>
              <span class="loading-text">正在思考...</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="input-area">
      <div v-if="uploadedFiles.length > 0" class="file-preview-list">
        <div v-for="(file, index) in uploadedFiles" :key="index" class="file-item">
          <i class="el-icon-document"></i>
          <span class="file-name">{{ file.name }}</span>
          <i class="el-icon-close remove-icon" @click="removeFile(index)"></i>
        </div>
      </div>
      <div class="input-wrapper">
        <el-button
          icon="el-icon-paperclip"
          type="text"
          class="attach-btn"
          @click="$refs.fileInput.click()"
        ></el-button>
        <input
          ref="fileInput"
          type="file"
          style="display: none"
          accept=".pdf,.doc,.docx,.txt"
          @change="handleFileSelect"
        />
        <el-input
          :value="input"
          @input="SET_INPUT($event)"
          placeholder="输入您的问题，或上传文档进行分析..."
          @keyup.enter.native="handleSend"
          class="message-input"
        ></el-input>
        <el-button
          type="primary"
          icon="el-icon-s-promotion"
          circle
          @click="handleSend"
          :disabled="!input.trim()"
          class="send-btn"
        ></el-button>
      </div>
      <p class="input-hint">💡 支持上传PDF、Word、TXT文档进行智能分析</p>
    </div>
  </div>
</template>

<script>
import { mapState, mapMutations, mapActions } from 'vuex'
import api from '@/api'
import mockService from '@/mock'
import AgentWorkflowInline from './AgentWorkflowInline.vue'

import { marked } from 'marked'
import DOMPurify from 'dompurify'

export default {
  name: 'ChatInterface',
  components: {
    AgentWorkflowInline
  },
  data() {
    return {
      uploadedFiles: [],
      serverFilename: ''
    }
  },
  computed: {
    ...mapState('chat', ['messages', 'input', 'isLoading'])
  },
  methods: {
    ...mapMutations('chat', ['SET_INPUT', 'ADD_MESSAGE', 'SET_LOADING']),
    ...mapActions('chat', ['sendMessage', 'sendMessageStream', 'sendReview']),

    async handleFileSelect(e) {
      const files = e.target.files
      if (files && files.length > 0) {
        const file = files[0]

        if (mockService.isEnabled()) {
          // Mock 模式：不上传，直接本地记录文件并切换模式
          this.uploadedFiles.push(file)
          this.serverFilename = file.name
          this.$store.commit('SET_TASK_MODE', 'document-review')
          this.$store.commit('SET_REVIEW_PHASE', 'document')
          this.$message.success('文件已选择（Mock模式）')
          e.target.value = ''
          return
        }

        try {
          // 上传文件到后端
          this.SET_LOADING(true)
          const uploadResponse = await api.uploadFile(file)

          this.uploadedFiles.push(file)
          this.serverFilename = uploadResponse.savefilename

          // 切换到文档审核模式
          this.$store.commit('SET_TASK_MODE', 'document-review')
          this.$store.commit('SET_REVIEW_PHASE', 'document')

          this.$message.success('文件上传成功')
        } catch (error) {
          console.error('文件上传失败:', error)
          this.$message.error('文件上传失败: ' + error.message)
        } finally {
          this.SET_LOADING(false)
          // 清空文件输入
          e.target.value = ''
        }
      }
    },

    removeFile(index) {
      this.uploadedFiles.splice(index, 1)
    },

    async handleSend() {
      if (!this.input.trim()) return

      const query = this.input
      const fileNames = this.uploadedFiles.map(f => f.name)
      const taskMode = this.$store.state.taskMode

      // 添加用户消息
      this.ADD_MESSAGE({
        id: Date.now().toString(),
        role: 'user',
        content: query,
        files: fileNames
      })

      this.SET_INPUT('')
      this.SET_LOADING(true)

      try {
        if (mockService.isEnabled()) {
          // ===== Mock 模式 =====
          if (taskMode === 'document-review') {
            await this.triggerDocumentReview(query)
          } else {
            await this.triggerKnowledgeQA(query)
          }
        } else {
          // ===== 真实 API 模式 =====
          if (taskMode === 'document-review' && this.serverFilename) {
            // 文档审核 → 调用 /api/review
            await this.sendReview({
              message: query,
              filename: this.serverFilename
            })
          } else {
            // 知识问答 → 调用 /api/chat/stream（降级到 /api/chat）
            await this.sendMessageStream({ message: query, mode: 'qa' })
          }
        }
      } catch (error) {
        console.error('API失败:', error)

        if (!mockService.isEnabled()) {
          try {
            // 流式失败降级到普通 /api/chat
            const response = await api.chat({ message: query, mode: 'qa' })
            this.ADD_MESSAGE({
              id: (Date.now() + 1).toString(),
              role: 'assistant',
              content: response.response || '未获取到回复'
            })
            this.SET_LOADING(false)
          } catch (fallbackError) {
            console.error('普通API也失败:', fallbackError)
            this.ADD_MESSAGE({
              id: Date.now().toString(),
              role: 'assistant',
              content: '抱歉，连接后端服务失败。请确保后端服务正在运行。'
            })
            this.SET_LOADING(false)
          }
        } else {
          this.ADD_MESSAGE({
            id: Date.now().toString(),
            role: 'assistant',
            content: '抱歉，发生错误: ' + error.message
          })
          this.SET_LOADING(false)
        }
      }

      // 清空上传的文件
      this.uploadedFiles = []
      this.serverFilename = ''
    },

    // 触发知识问答流程
    async triggerKnowledgeQA(message) {
      // 获取 Home 组件实例
      const homeInstance = this.getHomeInstance()

      // 判断是否使用内联模式（单栏）还是侧边栏模式（双栏）
      const useInlineMode = this.$store.state.layoutMode === 'single' || !homeInstance

      let assistantMessageContent = ''
      let workflowSteps = []
      const assistantMessageId = (Date.now() + 1).toString()

      // 添加空的助手消息，用于后续追加
      this.ADD_MESSAGE({
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        workflow: useInlineMode ? [] : undefined // 只在内联模式下添加workflow字段
      })

      try {
        await mockService.sendKnowledgeQAMessage(
          message,
          // 工作流更新回调
          (steps) => {
            workflowSteps = steps

            if (useInlineMode) {
              // 内联模式：更新消息中的workflow
              const lastMessage = this.$store.state.chat.messages[this.$store.state.chat.messages.length - 1]
              if (lastMessage && lastMessage.id === assistantMessageId) {
                lastMessage.workflow = [...steps]
              }
            } else {
              // 侧边栏模式：更新Home组件的workflowSteps
              if (homeInstance) {
                homeInstance.workflowSteps = steps
              }
            }
          },
          // 流式输出回调
          (chunk) => {
            assistantMessageContent = chunk
            // 更新最后一条消息
            const lastMessage = this.$store.state.chat.messages[this.$store.state.chat.messages.length - 1]
            if (lastMessage && lastMessage.id === assistantMessageId) {
              lastMessage.content = assistantMessageContent
            }
          }
        )
      } catch (error) {
        console.error('知识问答失败:', error)
        this.ADD_MESSAGE({
          id: Date.now().toString(),
          role: 'assistant',
          content: '知识问答过程中发生错误: ' + error.message
        })
      } finally {
        this.SET_LOADING(false)
      }
    },

    // 触发文档审核流程
    async triggerDocumentReview(message) {
      // 获取 DocumentReviewPanel 组件实例
      const reviewPanel = this.getReviewPanelInstance()
      const useInlineMode = this.$store.state.layoutMode === 'single' || !reviewPanel

      if (!reviewPanel && !useInlineMode) {
        console.error('无法找到 DocumentReviewPanel 组件')
        this.SET_LOADING(false)
        return
      }

      let assistantMessageContent = ''
      const assistantMessageId = (Date.now() + 1).toString()

      // 添加空的助手消息，用于后续追加
      this.ADD_MESSAGE({
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        workflow: useInlineMode ? [] : undefined // 单栏模式下添加workflow字段
      })

      try {
        await mockService.sendDocumentReviewMessageWithWorkflow(
          message,
          // 阶段变化回调
          (phase) => {
            if (reviewPanel) {
              reviewPanel.switchPhase(phase)
            }
            this.$store.commit('SET_REVIEW_PHASE', phase)
          },
          // 步骤更新回调
          (update) => {
            if (update.phase === 'document') {
              if (reviewPanel) {
                if (update.content) {
                  reviewPanel.updateDocumentContent(update.content)
                }
                if (update.scanning) {
                  reviewPanel.startScanning()
                }
              }
            } else if (update.phase === 'workflow') {
              // 双栏模式：更新侧边栏
              if (reviewPanel) {
                // 初始化工作流程（首次）
                if (update.step && !reviewPanel.workflowSteps.length) {
                  const conversation = mockService.getNextDocumentReviewConversation()
                  if (conversation && conversation.reviewData) {
                    reviewPanel.initWorkflow(conversation.reviewData.workflow.steps)
                  }
                }

                // 更新步骤状态
                if (typeof update.stepIndex !== 'undefined') {
                  reviewPanel.updateWorkflowStep(update.stepIndex, {
                    status: update.status,
                    progress: update.progress,
                    ...(update.progressItem && { progressItem: update.progressItem })
                  })
                }
              }

              // 单栏模式：更新消息中的workflow
              if (useInlineMode && update.workflowSteps) {
                const lastMessage = this.$store.state.chat.messages[this.$store.state.chat.messages.length - 1]
                if (lastMessage && lastMessage.id === assistantMessageId) {
                  lastMessage.workflow = [...update.workflowSteps]
                }
              }
            } else if (update.phase === 'result') {
              if (reviewPanel && update.report) {
                reviewPanel.updateFinalReport(update.report)
              }
            }
          },
          // 响应回调（流式输出）
          (chunk) => {
            assistantMessageContent += chunk
            // 更新最后一条消息
            const lastMessage = this.$store.state.chat.messages[this.$store.state.chat.messages.length - 1]
            if (lastMessage && lastMessage.id === assistantMessageId) {
              lastMessage.content = assistantMessageContent
            }
          }
        )
      } catch (error) {
        console.error('文档审核失败:', error)
        this.ADD_MESSAGE({
          id: Date.now().toString(),
          role: 'assistant',
          content: '文档审核过程中发生错误: ' + error.message
        })
      } finally {
        this.SET_LOADING(false)
      }
    },

    // 获取 DocumentReviewPanel 组件实例
    getReviewPanelInstance() {
      // 通过 parent 向上查找
      let parent = this.$parent
      while (parent) {
        if (parent.$children) {
          const reviewPanel = parent.$children.find(child =>
            child.$options.name === 'DocumentReviewPanel'
          )
          if (reviewPanel) {
            return reviewPanel
          }
        }
        parent = parent.$parent
      }

      // 通过 root 查找所有组件
      const findInChildren = (children) => {
        for (const child of children) {
          if (child.$options.name === 'DocumentReviewPanel') {
            return child
          }
          if (child.$children && child.$children.length > 0) {
            const found = findInChildren(child.$children)
            if (found) return found
          }
        }
        return null
      }

      return findInChildren(this.$root.$children)
    },

    // 获取 Home 组件实例
    getHomeInstance() {
      // 通过 parent 向上查找
      let parent = this.$parent
      while (parent) {
        if (parent.$options.name === 'Home') {
          return parent
        }
        parent = parent.$parent
      }
      return null
    },

    //markdown解析
    renderMarkdown(content) {
      if (!content) return ''
      // 解析 Markdown 为 HTML
      const rawHtml = marked(content)
      // 净化 HTML 防止 XSS 攻击
      return DOMPurify.sanitize(rawHtml)
    }
  },
  mounted() {
    // Mock 数据已准备好，等待用户手动触发
    // 不再自动加载示例对话
  }
}
</script>

<style scoped>
.chat-interface {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: transparent; /* 透出父容器背景图 */
}

/* 顶部 Header */
.right-header {
  height: 60px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
}

.agent-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.agent-avatar {
  width: 24px;
  height: 24px;
  background: #a5b4fc;
  border-radius: 50%;
  border: 1px solid white;
}

.agent-name {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.agent-status {
  font-size: 12px;
  color: #999;
}

.logo-text {
  font-size: 24px;
  font-weight: 900; /* 图1是非常粗的黑体 */
  color: #000;
  font-family: 'Inter', sans-serif;
}

.logo-icon {
  width: 28px;
}

/* 消息容器 */
.messages-container {
  flex: 1;
  padding: 30px;
  overflow-y: auto;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.message {
  display: flex;
  width: 100%;
}

.user-message {
  justify-content: flex-end;
}

/* 用户气泡：高亮橙色 */
.user-bubble {
  background-color: #f2994a !important;
  color: white !important;
  padding: 10px 20px;
  border-radius: 15px 15px 4px 15px; /* 对齐图1的非对称圆角 */
  font-size: 14px;
  box-shadow: 0 4px 10px rgba(242, 153, 74, 0.2);
}

/* 助手气泡：超大奶油色面板 */
.assistant-bubble {
  background-color: #fcf3e8 !important; /* 图1的标准奶粉色 */
  border-radius: 12px;
  padding: 24px;
  width: 100%; /* 助手回复通常占据横向大部分空间 */
  color: #333;
  box-shadow: 0 2px 15px rgba(0, 0, 0, 0.03);
}

.loading-bubble {
  width: fit-content; /* “正在思考”状态气泡较小 */
  padding: 12px 20px;
}

/* 正在思考动画 */
.loading-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.dots {
  display: flex;
  gap: 4px;
}

.dot {
  width: 6px;
  height: 6px;
  background: #3b82f6;
  border-radius: 50%;
  animation: loadingDot 1.4s infinite ease-in-out;
}

.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes loadingDot {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.loading-text {
  font-size: 14px;
  color: #888;
}

/* 底部输入框 */
.input-area {
  padding: 20px 30px 40px;
  background: transparent;
}

.input-wrapper {
  background: #fff;
  border-radius: 30px;
  display: flex;
  align-items: center;
  padding: 4px 6px 4px 15px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
  border: 1px solid #eee;
}

.message-input >>> .el-input__inner {
  border: none !important;
  background: transparent !important;
}

.attach-btn {
  font-size: 20px;
  color: #999;
}

.send-btn {
  background-color: #f2994a !important;
  border-color: #f2994a !important;
  width: 40px;
  height: 40px;
}

.input-hint {
  text-align: center;
  font-size: 12px;
  color: #aaa;
  margin-top: 10px;
}

/* Markdown 字体适配图1 */
.markdown-body {
  font-size: 15px;
  line-height: 1.8;
  color: #444;
}

/* 文件预览区域样式 */
.file-preview-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 10px 15px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(5px);
  border-radius: 12px;
  margin-bottom: 8px; /* 与输入框保持距离 */
  border: 1px solid rgba(0, 0, 0, 0.05);
  box-shadow: 0 -4px 15px rgba(0, 0, 0, 0.03); /* 向上微弱阴影 */
  max-height: 120px;
  overflow-y: auto;
  width: fit-content;
  max-width: 100%;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #fff;
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid #f2994a; /* 匹配你主题的橙色边框 */
  font-size: 13px;
  color: #333;
  animation: slideInUp 0.3s ease;
}

.file-name {
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-icon {
  cursor: pointer;
  color: #999;
  transition: color 0.2s;
}

.remove-icon:hover {
  color: #f56c6c;
}

/* 入场动画 */
@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 适配输入框布局 */
.input-area {
  display: flex;
  flex-direction: column;
  align-items: flex-start; /* 预览从左侧对齐 */
}

.input-wrapper {
  width: 100%; /* 确保输入条撑满 */
}

</style>