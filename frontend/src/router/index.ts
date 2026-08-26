// Vue Router 路由配置
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: () => import('@/views/ConsoleHome.vue') },
    { path: '/search', component: () => import('@/views/SearchPage.vue') },
    { path: '/forum', component: () => import('@/views/ForumPage.vue') },
    { path: '/graph-viewer', component: () => import('@/views/GraphViewer.vue') },
    { path: '/graph-viewer/:report_id', component: () => import('@/views/GraphViewer.vue') },
    { path: '/config', component: () => import('@/views/ConfigPage.vue') },
    { path: '/system', component: () => import('@/views/SystemStatus.vue') },
  ],
})

export default router
