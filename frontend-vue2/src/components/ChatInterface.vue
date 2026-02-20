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
              <p class="message-text">{{ message.content }}</p>
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
            v-model="input"
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

export default {
  name: 'ChatInterface',
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
        // 尝试使用流式API
        await this.sendMessageStream({ message: query })
      } catch (error) {
        console.error('流式API失败，降级到普通API:', error)

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
    }
  },
  mounted() {
    // 添加 Mock 数据用于演示
    this.ADD_MESSAGE({
      id: 'mock-1',
      role: 'user',
      content: '请帮我分析一下深度学习模型优化的最佳实践',
      files: []
    })

    this.ADD_MESSAGE({
      id: 'mock-2',
      role: 'assistant',
      content: '根据我的分析和搜索结果，深度学习模型优化的最佳实践包括以下几个方面：\n\n1. **学习率调整**：使用学习率衰减策略，如余弦退火或步进衰减\n2. **批量大小优化**：根据GPU内存选择合适的batch size\n3. **正则化技术**：应用Dropout、L2正则化等防止过拟合\n4. **数据增强**：通过数据增强提高模型泛化能力\n5. **模型架构**：选择合适的网络结构，考虑使用预训练模型\n\n这些建议综合了网络搜索结果和内部知识库的最佳实践。'
    })
  }
}
</script>

<style scoped>
.chat-interface {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
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
  overflow-y: auto;
  padding: 24px;
  padding-bottom: 140px;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
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
}

.assistant-message {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 85%;
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
  padding: 24px;
  background: linear-gradient(to top, white, rgba(255, 255, 255, 0.95));
  z-index: 20;
}

.input-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
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
  height: 56px;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 28px;
  display: flex;
  align-items: center;
  padding: 0 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: border-color 0.3s;
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
