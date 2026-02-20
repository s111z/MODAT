export default {
  namespaced: true,
  state: {
    steps: [],
    isActive: false
  },
  mutations: {
    ADD_STEP(state, step) {
      state.steps.push(step)
    },
    SET_STEPS(state, steps) {
      state.steps = steps
    },
    SET_ACTIVE(state, value) {
      state.isActive = value
    },
    CLEAR_STEPS(state) {
      state.steps = []
    }
  },
  actions: {
    addStep({ commit }, step) {
      commit('ADD_STEP', step)
    },
    setSteps({ commit }, steps) {
      commit('SET_STEPS', steps)
    },
    setActive({ commit }, value) {
      commit('SET_ACTIVE', value)
    },
    clearSteps({ commit }) {
      commit('CLEAR_STEPS')
    }
  }
}
