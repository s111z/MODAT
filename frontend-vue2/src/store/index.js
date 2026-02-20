import Vue from 'vue'
import Vuex from 'vuex'
import chat from './modules/chat'
import agent from './modules/agent'
import knowledge from './modules/knowledge'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    sidebarActive: 'chat', // 'chat' | 'history' | 'search' | 'knowledge'
    taskMode: 'qa',        // 'qa' | 'document-review'
    reviewPhase: 'document' // 'document' | 'workflow' | 'result'
  },
  mutations: {
    SET_SIDEBAR_ACTIVE(state, value) {
      state.sidebarActive = value
    },
    SET_TASK_MODE(state, mode) {
      state.taskMode = mode
    },
    SET_REVIEW_PHASE(state, phase) {
      state.reviewPhase = phase
    }
  },
  actions: {
    setSidebarActive({ commit }, value) {
      commit('SET_SIDEBAR_ACTIVE', value)
    },
    setTaskMode({ commit }, mode) {
      commit('SET_TASK_MODE', mode)
    },
    setReviewPhase({ commit }, phase) {
      commit('SET_REVIEW_PHASE', phase)
    }
  },
  modules: {
    chat,
    agent,
    knowledge
  }
})
