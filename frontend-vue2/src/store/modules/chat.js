import api from '@/api'

function getAgentStepMeta(content = '') {
  const text = String(content)
  const rules = [
    { test: /脱敏|敏感信息|PII/i, type: 'privacy', title: '信息脱敏' },
    { test: /意图|模式/i, type: 'intent', title: '意图识别' },
    { test: /Query|查询|处理查询|拆解/i, type: 'planning', title: '查询拆解' },
    { test: /知识库|相关文档|检索完成/i, type: 'searching', title: '知识库检索' },
    { test: /网络|web/i, type: 'web', title: '网络检索' },
    { test: /冲突|裁决|对齐/i, type: 'resolving', title: '冲突裁决' },
    { test: /生成回复|回复生成|生成完成/i, type: 'generating', title: '回复生成' }
  ]
  return rules.find(rule => rule.test.test(text)) || { type: 'thinking', title: '任务处理' }
}

export default {
  namespaced: true,
  state: {
    messages: [],
    input: '',
    isLoading: false,
    uploadedFiles: []
  },
  mutations: {
    ADD_MESSAGE(state, message) {
      state.messages.push(message)
    },
    SET_INPUT(state, value) {
      state.input = value
    },
    SET_LOADING(state, value) {
      state.isLoading = value
    },
    ADD_UPLOADED_FILE(state, file) {
      state.uploadedFiles.push(file)
    },
    CLEAR_UPLOADED_FILES(state) {
      state.uploadedFiles = []
    },
    UPDATE_LAST_MESSAGE(state, content) {
      if (state.messages.length > 0) {
        const lastMessage = state.messages[state.messages.length - 1]
        lastMessage.content += content
      }
    }
  },
  actions: {
    async sendMessage({ commit, state, rootState }) {
      commit('SET_LOADING', true)
      const message = state.input

      // 添加用户消息
      commit('ADD_MESSAGE', {
        id: Date.now().toString(),
        role: 'user',
        content: message,
        files: state.uploadedFiles.map(f => f.name)
      })

      commit('SET_INPUT', '')

      try {
        // 判断是否有文件上传，决定使用哪个模式
        const mode = rootState.taskMode
        const response = await api.chat({ message, mode })

        // 添加 AI 响应
        commit('ADD_MESSAGE', {
          id: Date.now().toString(),
          role: 'assistant',
          content: response.response,
          steps: response.steps
        })

        // 如果有步骤信息，更新 agent 模块
        if (response.steps && response.steps.length > 0) {
          commit('agent/SET_STEPS', response.steps.map((content, index) => ({
            id: `step-${index}`,
            type: 'thinking',
            content,
            timestamp: Date.now()
          })), { root: true })
        }
      } catch (error) {
        console.error('Chat error:', error)
        commit('ADD_MESSAGE', {
          id: Date.now().toString(),
          role: 'assistant',
          content: `抱歉，发生错误: ${error.message}`
        })
      } finally {
        commit('SET_LOADING', false)
        commit('CLEAR_UPLOADED_FILES')
      }
    },

    async sendMessageStream({ commit, state, rootState }, { message, mode, filename }) {
      commit('SET_LOADING', true)
      commit('agent/SET_ACTIVE', true, { root: true })

      commit('agent/ADD_STEP', {
        id: `round-${Date.now()}`,
        type: 'thinking',
        title: filename ? '继续文档问答' : '开始新问题',
        content: message,
        timestamp: Date.now()
      }, { root: true })

      if (filename) {
        commit('agent/ADD_STEP', {
          id: `doc-${Date.now()}`,
          type: 'parsing',
          title: '读取上传文档',
          content: '已接收上传文档，发送问题后将作为 Chatbot 的参考内容。',
          timestamp: Date.now()
        }, { root: true })
      }

      // 添加空的助手消息，后续追加内容
      const assistantMsgId = (Date.now() + 1).toString()
      commit('ADD_MESSAGE', {
        id: assistantMsgId,
        role: 'assistant',
        content: ''
      })

      try {
        await api.chatStream(
          { message, mode: mode || rootState.taskMode, filename },
          (event) => {
            // 处理流式数据
            if (event.type === 'response') {
              // 找到对应消息并替换完整内容
              const msg = state.messages.find(m => m.id === assistantMsgId)
              if (msg) {
                msg.content = event.content
              }
            } else if (event.type === 'step') {
              const meta = getAgentStepMeta(event.content)
              commit('agent/ADD_STEP', {
                id: `step-${Date.now()}-${state.messages.length}`,
                type: meta.type,
                title: meta.title,
                content: event.content,
                timestamp: Date.now()
              }, { root: true })
            } else if (event.type === 'error') {
              const msg = state.messages.find(m => m.id === assistantMsgId)
              if (msg) {
                msg.content = event.content || event.message || '抱歉，后端生成回复时遇到问题。'
              }
            }
          },
          (error) => {
            console.error('Stream error:', error)
          },
          () => {
            commit('SET_LOADING', false)
            commit('agent/SET_ACTIVE', false, { root: true })
          }
        )
      } catch (error) {
        console.error('Stream error:', error)
        commit('SET_LOADING', false)
        commit('agent/SET_ACTIVE', false, { root: true })
      }
    },

    /**
     * 发送文档审核请求（调用 /api/review）
     */
    async sendReview({ commit, state }, { message, filename }) {
      commit('SET_LOADING', true)

      // 添加空的助手消息
      const assistantMsgId = (Date.now() + 1).toString()
      commit('ADD_MESSAGE', {
        id: assistantMsgId,
        role: 'assistant',
        content: ''
      })

      try {
        const response = await api.review({
          filename,
          message,
          mode: 'review'
        })

        // 更新助手消息
        const msg = state.messages.find(m => m.id === assistantMsgId)
        if (msg) {
          msg.content = response.response
        }

        // 如果有步骤信息，更新 agent 模块
        if (response.steps && response.steps.length > 0) {
          commit('agent/SET_STEPS', response.steps.map((content, index) => ({
            id: `step-${index}`,
            type: 'thinking',
            content,
            timestamp: Date.now()
          })), { root: true })
        }

        return response
      } catch (error) {
        console.error('Review error:', error)
        const msg = state.messages.find(m => m.id === assistantMsgId)
        if (msg) {
          msg.content = `抱歉，文档审核发生错误: ${error.message}`
        }
        throw error
      } finally {
        commit('SET_LOADING', false)
        commit('CLEAR_UPLOADED_FILES')
      }
    }
  }
}
