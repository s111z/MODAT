import api from '@/api'

export default {
  namespaced: true,
  state: {
    documents: [],
    isLoading: false,
    searchResults: [],
    isSearching: false
  },
  mutations: {
    SET_DOCUMENTS(state, documents) {
      state.documents = documents
    },
    SET_LOADING(state, value) {
      state.isLoading = value
    },
    SET_SEARCH_RESULTS(state, results) {
      state.searchResults = results
    },
    SET_SEARCHING(state, value) {
      state.isSearching = value
    }
  },
  actions: {
    async fetchDocuments({ commit }, limit = 100) {
      commit('SET_LOADING', true)
      try {
        const response = await api.vectorDBList(limit)
        commit('SET_DOCUMENTS', response.results || [])
      } catch (error) {
        console.error('Fetch documents error:', error)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async searchDocuments({ commit }, query) {
      commit('SET_SEARCHING', true)
      try {
        const response = await api.vectorDBSearch({ query, top_k: 10 })
        commit('SET_SEARCH_RESULTS', response.results || [])
        return response.results
      } catch (error) {
        console.error('Search error:', error)
        throw error
      } finally {
        commit('SET_SEARCHING', false)
      }
    },

    async deleteDocument({ dispatch }, id) {
      try {
        await api.vectorDBDelete({ ids: [id] })
        // 重新加载列表
        await dispatch('fetchDocuments')
      } catch (error) {
        console.error('Delete error:', error)
        throw error
      }
    },

    async uploadAndAddDocument({ dispatch }, { file, metadatas }) {
      try {
        // 步骤 1: 上传文件
        const uploadResponse = await api.uploadKnowledgeFile(file)

        // 步骤 2: 添加到向量库
        const addResponse = await api.vectorDBAdd({
          filename: uploadResponse.savefilename,
          metadatas: metadatas || {
            category: 'general',
            permissions: 0
          }
        })

        // 重新加载列表
        await dispatch('fetchDocuments')

        return addResponse
      } catch (error) {
        console.error('Upload and add error:', error)
        throw error
      }
    },

    clearSearchResults({ commit }) {
      commit('SET_SEARCH_RESULTS', [])
    }
  },
  getters: {
    displayDocuments: (state) => {
      return state.searchResults.length > 0 ? state.searchResults : state.documents
    },
    totalDocuments: (state) => state.documents.length,
    searchResultsCount: (state) => state.searchResults.length
  }
}
