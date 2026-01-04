import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    // 登录路由
    {
      path: '/login',
      component: () => import('../layouts/AuthLayout.vue'),
      children: [
        {
          path: '',
          component: () => import('../views/Login.vue'),
          meta: { title: '登录' }
        }
      ]
    },
    // 应用主路由
    {
      path: '/',
      component: () => import('../layouts/AdminLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          redirect: '/dashboard'
        },
        {
          path: 'dashboard',
          component: () => import('../views/Dashboard.vue'),
          meta: { title: '仪表盘' }
        },
        {
          path: 'usage-analysis',
          component: () => import('../views/UsageAnalysis.vue'),
          meta: { title: '用电分析' }
        },
        {
          path: 'region-analysis',
          component: () => import('../views/RegionAnalysis.vue'),
          meta: { title: '片区分析', requiresAdmin: true }
        },
        {
          path: 'usage-management',
          component: () => import('../views/UsageManagement.vue'),
          meta: { title: '数据管理', requiresAdmin: true }
        },
        {
          path: 'admin',
          component: () => import('../views/Admin.vue'),
          meta: { title: '系统管理', requiresSuperAdmin: true }
        },
        {
          path: 'bills',
          component: () => import('../views/Bills.vue'),
          meta: { title: '账单管理' }
        },
        {
          path: 'settings',
          component: () => import('../views/Settings.vue'),
          meta: { title: '设置' }
        }
      ]
    },
    // 404
    {
      path: '/:pathMatch(.*)*',
      redirect: '/dashboard'
    }
  ]
})

// 导航守卫
router.beforeEach(async (to, from, next) => {
  console.log('路由守卫触发:', { to: to.path, from: from.path })
  const { isLoggedIn, user, initAuth } = useAuth()
  
  // 初始化认证状态
  initAuth()
  console.log('认证状态:', { isLoggedIn: isLoggedIn.value, user: user.value })
  
  // 需要登录的页面
  if (to.meta.requiresAuth) {
    console.log('需要登录的页面')
    if (!isLoggedIn.value) {
      console.log('未登录，重定向到登录页')
      next('/login')
      return
    }
    
    // 需要超级管理员权限
    if (to.meta.requiresSuperAdmin) {
      const userRole = user.value?.role || 'resident'
      if (userRole !== 'super_admin') {
        console.log('需要超级管理员权限，重定向到 dashboard')
        next('/dashboard')
        return
      }
    }
    
    // 需要管理员权限
    if (to.meta.requiresAdmin) {
      const userRole = user.value?.role || 'resident'
      const isAdmin = userRole === 'super_admin' || userRole === 'area_admin'
      if (!isAdmin) {
        console.log('权限不足，重定向到 dashboard')
        next('/dashboard')
        return
      }
    }
  }
  
  // 已登录用户访问登录页，重定向到首页
  if (to.path === '/login' && isLoggedIn.value) {
    console.log('已登录用户访问登录页，重定向到 dashboard')
    next('/dashboard')
    return
  }
  
  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - 用电信息系统`
  }
  
  console.log('允许访问:', to.path)
  next()
})

export default router
