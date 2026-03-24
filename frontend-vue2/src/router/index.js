import Vue from 'vue'
import VueRouter from 'vue-router'
import Home from '@/views/Home.vue'
import HomeSingle from '@/views/HomeSingle.vue'
import First from '@/views/First.vue'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'First',
    component: First
  },
  {
    path: '/content',
    name: 'Home',
    component: Home
  },
  {
    path: '/single',
    name: 'HomeSingle',
    component: HomeSingle
  }
  {
    path: '/knowledge',
    name: 'Knowledge',
    component: () => import('@/views/KnowledgeFiles.vue')
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
  // }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL || '/',
  routes
})

export default router
