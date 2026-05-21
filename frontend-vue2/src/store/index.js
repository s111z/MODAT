import Vue from 'vue'
import Vuex from 'vuex'
import chat from './modules/chat'
import agent from './modules/agent'
import knowledge from './modules/knowledge'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    sidebarActive: 'chat', // 'chat' | 'history' | 'search' | 'knowledge' | 'review'
    taskMode: 'qa',        // 'qa' | 'document-review'
    reviewPhase: 'document', // 'document' | 'workflow' | 'result'
    layoutMode: 'double'   // 'single' | 'double' - 单栏或双栏布局
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
    },
    SET_LAYOUT_MODE(state, mode) {
      state.layoutMode = mode
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
    },
    setLayoutMode({ commit }, mode) {
      commit('SET_LAYOUT_MODE', mode)
    }
  },
  modules: {
    chat,
    agent,
    knowledge
  }
})
