import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

/**
 * 路由元信息接口
 */
declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    requiresAuth?: boolean
    permission?: {
      modulePath: string
      operation: 'create' | 'read' | 'update' | 'delete' | 'export'
    }
  }
}

/**
 * 路由配置
 */
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        redirect: '/workbench'
      },
      {
        path: 'workbench',
        name: 'Workbench',
        component: () => import('@/views/Workbench.vue'),
        meta: { 
          title: '工作台',
          requiresAuth: true
        }
      },
      {
        path: 'announcements',
        name: 'Announcements',
        component: () => import('@/views/Announcements.vue'),
        meta: { 
          title: '公告栏',
          requiresAuth: true
        }
      }
    ]
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { 
      title: '登录', 
      requiresAuth: false 
    }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { 
      title: '注册', 
      requiresAuth: false 
    }
  },
  {
    path: '/scanner',
    name: 'Scanner',
    component: () => import('@/views/Scanner.vue'),
    meta: { 
      title: '扫码',
      requiresAuth: true
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { 
      title: '页面不存在',
      requiresAuth: false
    }
  }
]

/**
 * 创建路由实例
 */
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

/**
 * 全局前置守卫
 * 1. 验证 Token 有效性
 * 2. 检查路由权限
 * 3. 动态设置页面标题
 */
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.meta.requiresAuth !== false

  // 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - QMS 质量管理系统`
  }

  // 1. 检查是否需要登录
  if (requiresAuth && !authStore.isAuthenticated) {
    // 未登录用户重定向到登录页
    ElMessage.warning('请先登录')
    next({
      path: '/login',
      query: { redirect: to.fullPath }
    })
    return
  }

  // 2. 已登录用户访问登录/注册页时重定向到工作台
  if (!requiresAuth && authStore.isAuthenticated && (to.path === '/login' || to.path === '/register')) {
    next('/workbench')
    return
  }

  // 3. 检查路由权限（如果配置了 permission）
  if (requiresAuth && to.meta.permission) {
    const { modulePath, operation } = to.meta.permission
    
    try {
      const hasPermission = await authStore.checkPermission(modulePath, operation)
      
      if (!hasPermission) {
        ElMessage.error('权限不足，无法访问该页面')
        // 返回上一页或跳转到工作台
        if (from.path !== '/') {
          next(false)
        } else {
          next('/workbench')
        }
        return
      }
    } catch (error) {
      console.error('Permission check failed:', error)
      ElMessage.error('权限验证失败')
      next('/workbench')
      return
    }
  }

  // 4. 通过所有检查，允许访问
  next()
})

/**
 * 全局后置钩子
 * 用于页面加载完成后的处理
 */
router.afterEach((to) => {
  // 可以在这里添加页面访问统计等逻辑
  console.log(`Navigated to: ${to.path}`)
})

/**
 * 动态添加路由（用于根据权限动态渲染菜单）
 * @param routes 路由配置数组
 */
export function addDynamicRoutes(routes: RouteRecordRaw[]) {
  routes.forEach(route => {
    router.addRoute(route)
  })
}

/**
 * 重置路由（用于用户登出时清理动态路由）
 */
export function resetRouter() {
  const newRouter = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes
  })
  
  // 替换 matcher
  ;(router as any).matcher = (newRouter as any).matcher
}

export default router
