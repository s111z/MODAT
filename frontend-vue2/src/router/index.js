import Vue from 'vue'
import VueRouter from 'vue-router'
import Home from '@/views/Home.vue'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  }
  // 可扩展路由：
  // {
  //   path: '/chat',
  //   name: 'Chat',
  //   component: () => import('@/views/Chat.vue')
  // },
  // {
  //   path: '/history',
  //   name: 'History',
  //   component: () => import('@/views/History.vue')
  // },
  // {
  //   path: '/knowledge',
  //   name: 'Knowledge',
  //   component: () => import('@/views/Knowledge.vue')
  // }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL || '/',
  routes
})

export default router
