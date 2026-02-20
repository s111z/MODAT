import api from '@/api'

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

    async sendMessageStream({ commit, state, rootState }, { message, mode }) {
      commit('SET_LOADING', true)

      // 添加用户消息
      commit('ADD_MESSAGE', {
        id: Date.now().toString(),
        role: 'user',
        content: message
      })

      // 添加空的助手消息，后续追加内容
      commit('ADD_MESSAGE', {
        id: Date.now().toString(),
        role: 'assistant',
        content: ''
      })

      try {
        await api.chatStream(
          { message, mode: mode || rootState.taskMode },
          (event) => {
            // 处理流式数据
            if (event.type === 'response') {
              commit('UPDATE_LAST_MESSAGE', event.content)
            } else if (event.type === 'step') {
              commit('agent/ADD_STEP', {
                id: `step-${Date.now()}`,
                type: event.type,
                content: event.content,
                timestamp: Date.now()
              }, { root: true })
            }
          },
          (error) => {
            console.error('Stream error:', error)
          },
          () => {
            commit('SET_LOADING', false)
          }
        )
      } catch (error) {
        console.error('Stream error:', error)
        commit('SET_LOADING', false)
      }
    }
  }
}
