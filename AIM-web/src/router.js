import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('./views/Login.vue')
  },
  {
    path: '/',
    name: 'MainLayout',
    component: () => import('./views/MainLayout.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/knowledge',
    name: 'KnowledgeBase',
    component: () => import('./views/KnowledgeBase.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  
  if (to.meta.requiresAuth && !token) {
    // 需要登录但未登录，跳转到登录页
    next('/login')
  } else if (to.path === '/login' && token) {
    // 已登录访问登录页，跳转到主页
    next('/')
  } else {
    next()
  }
})

export default router
