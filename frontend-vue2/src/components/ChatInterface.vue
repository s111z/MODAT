<template>
  <div class="chat-interface">
    <div class="right-header">
      <div class="agent-info">
        <div class="agent-avatar" aria-hidden="true">
          <svg
            class="scales-icon"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path d="M12 4V19" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
            <path d="M8 19H16" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
            <path d="M6 7H18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
            <path d="M6 7L3.5 13H8.5L6 7Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" />
            <path d="M18 7L15.5 13H20.5L18 7Z" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round" />
            <path d="M3.5 13C3.95 14.25 4.85 15 6 15C7.15 15 8.05 14.25 8.5 13" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
            <path d="M15.5 13C15.95 14.25 16.85 15 18 15C19.15 15 20.05 14.25 20.5 13" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
          </svg>
        </div>
        <div class="agent-text">
          <div class="agent-name">Compliance Copilot</div>
          <div class="agent-status">
            <span class="status-dot"></span>
            <span>您的AI助手已就绪</span>
          </div>
        </div>
      </div>
      
      <div class="header-logo">
        <span class="logo-text">MOTA</span>
        <span class="logo-badge">
          <img src="@/assets/images/logo.png" alt="Mota" class="logo-icon" />
        </span>
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

          <div
            v-else-if="hasAssistantVisibleContent(message)"
            class="message assistant-message"
          >
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
          @click="openChatFilePicker"
        ></el-button>
        <input
          ref="fileInput"
          type="file"
          style="display: none"
          accept=".pdf,.doc,.docx,.txt"
          @change="handleFileSelect"
        />
        <el-input
          type="textarea"
          :value="input"
          @input="SET_INPUT($event)"
          placeholder="输入您的问题，或上传文档进行分析..."
          :autosize="{ minRows: 1, maxRows: 8 }"
          @keydown.enter.native.exact.prevent="handleSend"
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
      serverFilename: '',
      nextFileAction: 'chat'
    }
  },
  computed: {
    ...mapState('chat', ['messages', 'input', 'isLoading'])
  },
  methods: {
    ...mapMutations('chat', ['SET_INPUT', 'ADD_MESSAGE', 'SET_LOADING']),
    ...mapActions('chat', ['sendMessage', 'sendMessageStream', 'sendReview']),

    createAssistantMessage(content = '') {
      const id = (Date.now() + 1).toString()
      this.ADD_MESSAGE({
        id,
        role: 'assistant',
        content
      })
      return id
    },

    hasAssistantVisibleContent(message) {
      return Boolean(
        (message.content && message.content.trim()) ||
        (message.workflow && message.workflow.length > 0)
      )
    },

    openReviewFilePicker() {
      this.nextFileAction = 'review'
      if (this.$refs.fileInput) {
        this.$refs.fileInput.click()
      }
    },

    openChatFilePicker() {
      this.nextFileAction = 'chat'
      if (this.$refs.fileInput) {
        this.$refs.fileInput.click()
      }
    },

    async handleFileSelect(e) {
      const files = e.target.files
      if (files && files.length > 0) {
        const file = files[0]
        const defaultReviewMessage = '请审核这份方案'
        const shouldStartReview = this.nextFileAction === 'review'

        if (mockService.isEnabled()) {
          this.uploadedFiles = [file]
          this.serverFilename = file.name
          if (shouldStartReview) {
            this.$store.commit('SET_TASK_MODE', 'document-review')
            this.$store.commit('SET_REVIEW_PHASE', 'document')
            this.$message.success('文件已选择，开始自动审核')
            e.target.value = ''
            await this.startReview(defaultReviewMessage, { autoAddUserMessage: true })
          } else {
            this.$store.commit('SET_TASK_MODE', 'qa')
            this.$message.success('文件已选择，请输入你的问题后发送')
          }
          e.target.value = ''
          this.nextFileAction = 'chat'
          return
        }

        try {
          this.SET_LOADING(true)
          const uploadResponse = await api.uploadFile(file)

          this.uploadedFiles = [file]
          this.serverFilename = uploadResponse.savefilename

          if (shouldStartReview) {
            this.$store.commit('SET_TASK_MODE', 'document-review')
            this.$store.commit('SET_REVIEW_PHASE', 'document')
            this.$message.success('文件上传成功，开始自动审核')
            this.SET_LOADING(false)
            await this.$nextTick()
            await this.startReview(defaultReviewMessage, { autoAddUserMessage: true })
          } else {
            this.$store.commit('SET_TASK_MODE', 'qa')
            this.$message.success('文件上传成功，请输入你的问题后发送')
          }
        } catch (error) {
          console.error('文件上传或审核失败:', error)
          this.$message.error('文件上传或审核失败: ' + error.message)
        } finally {
          this.SET_LOADING(false)
          e.target.value = ''
          this.nextFileAction = 'chat'
        }
      }
    },

    removeFile(index) {
      this.uploadedFiles.splice(index, 1)
      if (this.uploadedFiles.length === 0) {
        this.serverFilename = ''
      }
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
        if (taskMode === 'document-review' && this.serverFilename) {
          await this.startReview(query)
        } else if (mockService.isEnabled()) {
          await this.triggerKnowledgeQA(query)
        } else {
          // 知识问答 → 调用 /api/chat/stream（降级到 /api/chat）
          await this.sendMessageStream({
            message: query,
            mode: 'qa',
            filename: this.serverFilename || undefined
          })
          this.uploadedFiles = []
          this.serverFilename = ''
        }
      } catch (error) {
        console.error('API失败:', error)

        if (!mockService.isEnabled() && !(taskMode === 'document-review' && this.serverFilename)) {
          try {
            // 流式失败降级到普通 /api/chat
            const response = await api.chat({
              message: query,
              mode: 'qa',
              filename: this.serverFilename || undefined
            })
            this.ADD_MESSAGE({
              id: (Date.now() + 1).toString(),
              role: 'assistant',
              content: response.response || '未获取到回复'
            })
            this.uploadedFiles = []
            this.serverFilename = ''
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
    },

    // 触发方案审核流程
    async startReview(message, options = {}) {
      if (options.autoAddUserMessage) {
        this.ADD_MESSAGE({
          id: Date.now().toString(),
          role: 'user',
          content: message,
          files: this.uploadedFiles.map(f => f.name)
        })
      }

      if (mockService.isEnabled()) {
        await this.triggerDocumentReview(message)
        this.uploadedFiles = []
        this.serverFilename = ''
        return
      }

      if (!this.serverFilename) {
        throw new Error('缺少已上传文件，请先上传方案文件')
      }

      const reviewPanel = this.getReviewPanelInstance()
      if (reviewPanel) {
        if (reviewPanel.resetReviewState) reviewPanel.resetReviewState('workflow')
        reviewPanel.switchPhase('workflow')
        reviewPanel.initWorkflow(this.buildPendingReviewWorkflow())
      }
      this.$store.commit('SET_REVIEW_PHASE', 'workflow')

      await api.reviewStream(
        {
          message,
          filename: this.serverFilename,
          mode: 'review'
        },
        this.handleReviewEvent,
        this.handleReviewError,
        this.handleReviewComplete
      )

      this.uploadedFiles = []
      this.serverFilename = ''
    },

    buildPendingReviewWorkflow() {
      return [
        { id: 'doc-analysis', name: '读取文档', icon: '', status: 'in_progress', details: null },
        { id: 'schema-extraction', name: '提取关键信息', icon: '', status: 'pending', details: { fields: [] } },
        { id: 'query-construction', name: '构建查询问题', icon: '', status: 'pending', details: { queries: [] } },
        { id: 'multi-source-pk', name: '多源检索与裁决', icon: '', status: 'pending', details: { analysis: [] } },
        { id: 'quality-check', name: '审核自查', icon: '', status: 'pending', details: { checks: [] } },
        { id: 'plan-rewrite', name: '方案优化', icon: '', status: 'pending', details: { sections: [] } },
        { id: 'report-generation', name: '生成审核报告', icon: '', status: 'pending', details: { sections: ['审核概要', '风险分析', '问题建议', '审核结论'] } }
      ]
    },

    handleReviewEvent(event) {
      const reviewPanel = this.getReviewPanelInstance()
      if (!reviewPanel || !event) return

      switch (event.type) {
        case 'meta':
          if (reviewPanel.resetReviewState) reviewPanel.resetReviewState('workflow')
          if (event.fileName) reviewPanel.updateFileName(event.fileName)
          this.$store.commit('SET_REVIEW_PHASE', 'workflow')
          break
        case 'workflow_init':
          reviewPanel.initWorkflow(event.steps || [])
          reviewPanel.switchPhase('workflow')
          this.$store.commit('SET_REVIEW_PHASE', 'workflow')
          break
        case 'node_start':
          reviewPanel.patchWorkflowStep(event.stepId, { status: 'in_progress' })
          if (event.message) reviewPanel.appendNodeLog(event.stepId, event.message)
          break
        case 'node_log':
          if (event.stepId) reviewPanel.appendNodeLog(event.stepId, event.message)
          break
        case 'command_log':
          if (reviewPanel.appendCommandLog) reviewPanel.appendCommandLog(event)
          break
        case 'document_patch':
          reviewPanel.patchDocumentContent(event.content || '', event.documentInfo || {})
          break
        case 'document_chunk':
          reviewPanel.appendDocumentContent(event.content || '', event.documentInfo || {})
          break
        case 'step_patch':
          reviewPanel.patchWorkflowStep(event.stepId, event.patch || {})
          break
        case 'report_chunk':
          reviewPanel.appendReportChunk(event.section, event.content || '')
          break
        case 'report_item':
          reviewPanel.appendReportItem(event.section, event.item)
          break
        case 'optimization_chunk':
          reviewPanel.appendOptimizationChunk(event)
          break
        case 'result_snapshot':
          if (event.resultSnapshot) reviewPanel.patchFinalReport(event.resultSnapshot)
          break
        case 'final':
          if (event.reviewData) {
            this.applyReviewResponse({ reviewData: event.reviewData, fileName: event.fileName })
          } else if (event.resultSnapshot) {
            reviewPanel.patchFinalReport(event.resultSnapshot)
          }
          reviewPanel.switchPhase('result')
          this.$store.commit('SET_REVIEW_PHASE', 'result')
          this.ADD_MESSAGE({
            id: Date.now().toString(),
            role: 'assistant',
            content: event.message || '审核完成，已在左侧生成审核报告和方案优化建议。'
          })
          this.SET_LOADING(false)
          break
        case 'error':
          if (event.stepId) reviewPanel.patchWorkflowStep(event.stepId, { status: 'error' })
          this.ADD_MESSAGE({
            id: Date.now().toString(),
            role: 'assistant',
            content: '审核失败：' + (event.message || '未知错误')
          })
          this.SET_LOADING(false)
          break
      }
    },

    handleReviewError(error) {
      console.error('审核流错误:', error)
      this.ADD_MESSAGE({
        id: Date.now().toString(),
        role: 'assistant',
        content: '审核流式接口失败：' + (error && error.message ? error.message : '未知错误')
      })
      this.SET_LOADING(false)
    },

    handleReviewComplete() {
      this.SET_LOADING(false)
    },

    applyReviewResponse(response) {
      const reviewPanel = this.getReviewPanelInstance()
      const reviewData = response && response.reviewData

      if (!reviewPanel || !reviewData) {
        return
      }

      if (reviewData.documentContent) {
        reviewPanel.updateDocumentContent(reviewData.documentContent)
      }
      if (reviewData.fileName || response.fileName) {
        reviewPanel.updateFileName(reviewData.fileName || response.fileName)
      }
      if (reviewData.workflow && reviewData.workflow.steps) {
        reviewPanel.initWorkflow(reviewData.workflow.steps)
        reviewPanel.markPhaseAsCompleted('workflow')
      }
      if (reviewData.finalReport) {
        reviewPanel.updateFinalReport(reviewData.finalReport)
      }
      const rewriteNode = (reviewData.workflow && reviewData.workflow.steps || []).find(step => step.id === 'plan-rewrite')
      if (rewriteNode && rewriteNode.status === 'done') {
        reviewPanel.markPhaseAsCompleted('optimization')
      }
      reviewPanel.switchPhase('result')
      this.$store.commit('SET_REVIEW_PHASE', 'result')
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
                if (update.fileName) {
                  reviewPanel.updateFileName(update.fileName)
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
  height: 68px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 32px;
  background: linear-gradient(180deg, #FDFBF9 0%, #FAF7F2 100%);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid #F1E7D8;
}

.agent-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.agent-avatar {
  width: 40px;
  height: 40px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 40px;
  color: #6B4423;
  background: #F3EFE9;
  border-radius: 12px;
  border: 1px solid rgba(107, 68, 35, 0.08);
}

.scales-icon {
  width: 24px;
  height: 24px;
}

.agent-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.agent-name {
  font-size: 14px;
  font-weight: 600;
  color: #3C2F2F;
}

.agent-status {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 12px;
  color: #8B7E74;
}

.status-dot {
  width: 6px;
  height: 6px;
  position: relative;
  flex: 0 0 6px;
  border-radius: 50%;
  background: #8B5E34;
}

.status-dot::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: rgba(139, 94, 52, 0.28);
  animation: statusPing 2.4s ease-out infinite;
}

.header-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  line-height: 1;
}

.logo-text {
  font-size: 24px;
  font-weight: 900;
  font-family: 'Times New Roman', 'PingFang SC', 'Microsoft YaHei', serif;
  letter-spacing: 2px;
  position: relative;
  display: inline-block;
  background: linear-gradient(
    110deg,
    #4a3a32 0%,
    #4a3a32 44%,
    rgba(255, 255, 255, 0.88) 49%,
    #4a3a32 54%,
    #4a3a32 100%
  );
  background-size: 360% 100%;
  background-position: 210% 0;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
  animation: logoShimmer 18s linear infinite;
}

.logo-badge {
  width: 48px;
  height: 48px;
  padding: 6px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #f7efe4;
  border-radius: 50%;
  overflow: hidden;
  flex: 0 0 48px;
}

.logo-icon {
  width: 36px;
  height: 36px;
  display: block;
  object-fit: contain;
  position: relative;
  top: 0;
  transform-origin: 50% 80%;
  animation: otterBounce 18s ease-in-out infinite;
}

@keyframes logoShimmer {
  0%, 42% {
    background-position: 210% 0;
  }
  88% {
    background-position: -150% 0;
  }
  88.01%, 100% {
    background-position: 210% 0;
  }
}

@keyframes otterBounce {
  0%, 66%, 100% {
    transform: translateY(0) scale(1);
  }
  74% {
    transform: translateY(-6px) scale(1.04);
  }
  79% {
    transform: translateY(0) scale(0.98);
  }
  84% {
    transform: translateY(-3px) scale(1.02);
  }
  88% {
    transform: translateY(0) scale(1);
  }
}

@keyframes statusPing {
  0% {
    opacity: 0.55;
    transform: scale(1);
  }
  80%, 100% {
    opacity: 0;
    transform: scale(3);
  }
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
  gap: 18px;
}

.message {
  display: flex;
  width: 100%;
}

.user-message {
  justify-content: flex-end;
}

/* 用户气泡：深棕色 */
.user-bubble {
  background-color: #B8733E !important;
  color: white !important;
  padding: 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
  box-shadow: 0 4px 12px rgba(139, 69, 19, 0.10);
}

/* 助手气泡：极浅米白色 */
.assistant-bubble {
  background-color: #FFF9F0 !important;
  border-radius: 12px;
  padding: 16px;
  width: 100%; /* 助手回复通常占据横向大部分空间 */
  color: #333;
  box-shadow: 0 4px 12px rgba(139, 69, 19, 0.05);
  font-size: 14px;
  line-height: 1.6;
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
  background: #F8EBDD;
  border-radius: 999px;
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 10px 12px 10px 16px;
  box-shadow: 0 4px 12px rgba(139, 69, 19, 0.05);
  border: 1px solid #E8D5C4;
  transition: box-shadow 0.2s ease, background-color 0.2s ease;
}

.message-input {
  flex: 1;
}

.message-input >>> .el-textarea__inner {
  border: none !important;
  background: transparent !important;
  resize: none;
  min-height: 40px !important;
  max-height: 200px;
  padding: 9px 4px;
  box-shadow: none !important;
  font-size: 14px;
  line-height: 1.6;
  color: #4a3a28;
  overflow-y: auto;
}

.message-input >>> .el-textarea__inner::placeholder {
  color: #b8aa9b;
}

.attach-btn {
  font-size: 20px;
  color: #9d8d7f;
  height: 40px;
  width: 36px;
  flex-shrink: 0;
}

.attach-btn:hover {
  color: #B8733E;
}

.send-btn {
  background-color: #f2994a !important;
  border-color: #f2994a !important;
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease;
}

.send-btn:hover:not(.is-disabled) {
  transform: scale(1.08);
  box-shadow: 0 6px 16px rgba(184, 115, 62, 0.22);
  background-color: #E88935 !important;
  border-color: #E88935 !important;
}

.input-hint {
  text-align: center;
  font-size: 12px;
  color: #aaa;
  margin-top: 10px;
}

/* Markdown 字体适配图1 */
.markdown-body {
  font-size: 14px;
  line-height: 1.6;
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
  border: 1px solid #E8D5C4;
  box-shadow: 0 4px 12px rgba(139, 69, 19, 0.05);
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
  border-radius: 12px;
  border: 1px solid #E8D5C4;
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
