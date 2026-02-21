<template>
  <div class="chat-interface">
    <!-- 顶部状态栏 -->
    <div class="status-bar">
      <div class="status-indicator">
        <div :class="['status-dot', { 'loading': isLoading }]"></div>
      </div>
      <div class="status-info">
        <div class="status-title">Compliance Copilot</div>
        <div class="status-text">{{ isLoading ? 'Processing...' : 'Ready' }}</div>
      </div>
    </div>

    <!-- 对话区域 -->
    <div class="messages-container">
      <div class="messages-list">
        <div v-for="message in messages" :key="message.id" class="message-item">
          <!-- 用户消息 -->
          <div v-if="message.role === 'user'" class="message user-message">
            <div class="message-bubble user-bubble">
              <p class="message-text">{{ message.content }}</p>
              <div v-if="message.files && message.files.length > 0" class="message-files">
                📎 {{ message.files.join(', ') }}
              </div>
            </div>
          </div>

          <!-- 助手消息 -->
          <div v-else class="message assistant-message">
            <div class="message-bubble assistant-bubble">
              <!-- 工作流展示（如果有） -->
              <AgentWorkflowInline
                v-if="message.workflow && message.workflow.length > 0"
                :steps="message.workflow"
                class="message-workflow"
              />
              <!-- 消息内容 -->
              <p v-if="message.content" class="message-text">{{ message.content }}</p>
            </div>
          </div>
        </div>

        <!-- 加载指示器 -->
        <div v-if="isLoading" class="message assistant-message">
          <div class="message-bubble assistant-bubble">
            <div class="loading-dots">
              <div class="dot" style="animation-delay: 0ms"></div>
              <div class="dot" style="animation-delay: 150ms"></div>
              <div class="dot" style="animation-delay: 300ms"></div>
              <span class="loading-text">正在思考...</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部输入区域 -->
    <div class="input-area">
      <div class="input-container">
        <!-- 已上传文件 -->
        <div v-if="uploadedFiles.length > 0" class="uploaded-files">
          <div
            v-for="(file, index) in uploadedFiles"
            :key="index"
            class="file-tag"
          >
            <span class="file-name">{{ file.name }}</span>
            <el-button
              type="text"
              icon="el-icon-close"
              size="mini"
              @click="removeFile(index)"
              class="remove-btn"
            ></el-button>
          </div>
        </div>

        <!-- 输入框 -->
        <div class="input-wrapper">
          <input
            ref="fileInput"
            type="file"
            style="display: none"
            accept=".pdf,.doc,.docx,.txt"
            @change="handleFileSelect"
          />
          <el-button
            icon="el-icon-paperclip"
            circle
            size="small"
            @click="$refs.fileInput.click()"
            :disabled="isLoading"
            class="attach-btn"
          ></el-button>

          <el-input
            :value="input"
            @input="SET_INPUT($event)"
            placeholder="输入您的问题，或上传文档进行分析..."
            :disabled="isLoading"
            @keyup.enter.native="handleSend"
            class="message-input"
          ></el-input>

          <el-button
            type="primary"
            icon="el-icon-s-promotion"
            circle
            @click="handleSend"
            :disabled="isLoading || !input.trim()"
            class="send-btn"
          ></el-button>
        </div>

        <p class="input-hint">💡 支持上传PDF、Word、TXT文档进行智能分析</p>
      </div>
    </div>
  </div>
</template>

<script>
import { mapState, mapMutations, mapActions } from 'vuex'
import api from '@/api'
import mockService from '@/mock'
import AgentWorkflowInline from './AgentWorkflowInline.vue'

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
    ...mapActions('chat', ['sendMessage', 'sendMessageStream']),

    async handleFileSelect(e) {
      const files = e.target.files
      if (files && files.length > 0) {
        const file = files[0]

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
        // 判断是否为文档审核模式
        if (taskMode === 'document-review' && mockService.isEnabled()) {
          // 触发文档审核流程
          await this.triggerDocumentReview(query)
        } else if (mockService.isEnabled() && taskMode === 'qa') {
          // 知识问答模式 - 使用Mock
          await this.triggerKnowledgeQA(query)
        } else {
          // 真实API调用 - 尝试使用流式API
          await this.sendMessageStream({ message: query })
        }
      } catch (error) {
        console.error('API失败:', error)

        try {
          // 降级到普通API
          await this.sendMessage()
        } catch (fallbackError) {
          console.error('普通API也失败:', fallbackError)
          this.ADD_MESSAGE({
            id: Date.now().toString(),
            role: 'assistant',
            content: '抱歉，连接后端服务失败。请确保后端服务正在运行。'
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
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  position: relative;
}

/* 顶部状态栏 */
.status-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  border-bottom: 1px solid #e0e0e0;
  background: #f9fafb;
  z-index: 10;
}

.status-indicator {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #e0f2fe 0%, #c7d2fe 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #d1d5db;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #9ca3af;
}

.status-dot.loading {
  background: #3b82f6;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-title {
  font-weight: 600;
  font-size: 14px;
  color: #111827;
}

.status-text {
  font-size: 12px;
  color: #6b7280;
  font-family: 'Monaco', 'Courier New', monospace;
}

/* 对话区域 */
.messages-container {
  flex: 1;
  width: 100%;
  overflow-y: auto;
  padding: 24px;
  padding-bottom: 200px;
  box-sizing: border-box;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 100%;
  width: 100%;
}

.message-item {
  animation: fadeIn 0.5s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message {
  display: flex;
}

.user-message {
  justify-content: flex-end;
  width: 100%;
}

.user-message .message-bubble {
  max-width: 70%;
}

.assistant-message {
  justify-content: flex-start;
  width: 100%;
}

.assistant-message .message-bubble {
  width: 100%;
  max-width: 100%;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.user-bubble {
  background: #3b82f6;
  color: white;
}

.assistant-bubble {
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  color: #111827;
}

.message-text {
  font-size: 14px;
  white-space: pre-wrap;
  line-height: 1.6;
  margin: 0;
}

.message-workflow {
  margin-bottom: 12px;
}

.message-files {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.3);
  font-size: 12px;
}

/* 加载动画 */
.loading-dots {
  display: flex;
  align-items: center;
  gap: 8px;
}

.dot {
  width: 8px;
  height: 8px;
  background: #3b82f6;
  border-radius: 50%;
  animation: bounce 1s ease-in-out infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.loading-text {
  font-size: 14px;
  color: #6b7280;
  margin-left: 8px;
}

/* 底部输入区域 */
.input-area {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  width: 100%;
  padding: 24px;
  background: linear-gradient(to top, white, rgba(255, 255, 255, 0.95));
  z-index: 20;
  box-sizing: border-box;
}

.input-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  max-width: 100%;
}

.uploaded-files {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.file-tag {
  display: flex;
  align-items: center;
  gap: 8px;
  background: white;
  border: 1px solid #d1d5db;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  color: #374151;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.file-name {
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-btn {
  padding: 0;
  min-width: auto;
  color: #9ca3af;
}

.remove-btn:hover {
  color: #ef4444;
}

.input-wrapper {
  width: 100%;
  height: 56px;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 28px;
  display: flex;
  align-items: center;
  padding: 0 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: border-color 0.3s;
  box-sizing: border-box;
}

.input-wrapper:hover {
  border-color: #9ca3af;
}

.attach-btn {
  color: #6b7280;
  margin-right: 4px;
}

.message-input {
  flex: 1;
}

.message-input >>> .el-input__inner {
  border: none;
  background: transparent;
  color: #111827;
  padding: 0 12px;
}

.message-input >>> .el-input__inner:focus {
  box-shadow: none;
}

.message-input >>> .el-input__inner::placeholder {
  color: #9ca3af;
}

.send-btn {
  width: 44px;
  height: 44px;
  background: #3b82f6;
  border: none;
  transition: all 0.3s;
}

.send-btn:hover {
  background: #2563eb;
  transform: scale(1.05);
}

.send-btn:disabled {
  opacity: 0.5;
  transform: scale(1);
}

.input-hint {
  font-size: 12px;
  color: #6b7280;
  text-align: center;
  margin: 0;
  padding: 0 16px;
}
</style>
