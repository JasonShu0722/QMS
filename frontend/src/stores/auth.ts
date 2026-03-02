import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types/user'

/**
 * 认证状态管理 Store
 * 管理用户登录状态、Token、用户信息和权限检查
 */
export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const userInfo = ref<User | null>(null)
  // 当前登录环境（stable = 正式版，preview = 预览版）
  const currentEnvironment = ref<string>(localStorage.getItem('current_environment') || 'stable')

  // Computed
  const isAuthenticated = computed(() => !!token.value)
  const isSupplier = computed(() => userInfo.value?.user_type === 'supplier')
  const isInternal = computed(() => userInfo.value?.user_type === 'internal')
  const isPreviewEnv = computed(() => currentEnvironment.value === 'preview')

  /**
   * 初始化用户信息（从 localStorage 恢复）
   */
  function initUserInfo() {
    const storedUserInfo = localStorage.getItem('user_info')
    if (storedUserInfo) {
      try {
        userInfo.value = JSON.parse(storedUserInfo)
      } catch (error) {
        console.error('Failed to parse user info from localStorage:', error)
        logout()
      }
    }
  }

  /**
   * 用户登录
   * @param username 用户名
   * @param password 密码
   * @param userType 用户类型 (internal/supplier)
   * @param captcha 图形验证码（供应商登录必填）
   * @param captchaId 验证码ID（供应商登录必填）
   * @param environment 登录目标环境（stable/preview，默认 stable）
   */
  async function login(
    username: string,
    password: string,
    userType: 'internal' | 'supplier',
    captcha?: string,
    captchaId?: string,
    environment: string = 'stable'
  ): Promise<void> {
    // 动态导入避免循环依赖
    const { authApi } = await import('@/api/auth')

    const response = await authApi.login({
      username,
      password,
      user_type: userType,
      captcha,
      captcha_id: captchaId,
      environment
    })

    // 保存 Token、用户信息和当前环境
    token.value = response.access_token
    userInfo.value = response.user_info
    currentEnvironment.value = response.environment || environment

    localStorage.setItem('access_token', response.access_token)
    localStorage.setItem('user_info', JSON.stringify(response.user_info))
    localStorage.setItem('current_environment', currentEnvironment.value)
  }

  /**
   * 用户登出
   */
  function logout() {
    token.value = null
    userInfo.value = null
    currentEnvironment.value = 'stable'
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_info')
    localStorage.removeItem('current_environment')
  }

  /**
   * 检查用户是否有指定权限
   * @param modulePath 功能模块路径 (如: "supplier.performance.monthly_score")
   * @param operation 操作类型 (create/read/update/delete/export)
   * @returns 是否有权限
   */
  async function checkPermission(
    modulePath: string,
    operation: 'create' | 'read' | 'update' | 'delete' | 'export'
  ): Promise<boolean> {
    if (!isAuthenticated.value || !userInfo.value) {
      return false
    }

    try {
      // 动态导入避免循环依赖
      const { authApi } = await import('@/api/auth')
      return await authApi.checkPermission(modulePath, operation)
    } catch (error) {
      console.error('Permission check failed:', error)
      return false
    }
  }

  /**
   * 刷新用户信息（从后端重新获取）
   */
  async function refreshUserInfo(): Promise<void> {
    if (!isAuthenticated.value) {
      return
    }

    try {
      const { authApi } = await import('@/api/auth')
      const response = await authApi.getCurrentUser()
      userInfo.value = response
      localStorage.setItem('user_info', JSON.stringify(response))
    } catch (error) {
      console.error('Failed to refresh user info:', error)
      // Token 可能已失效，执行登出
      logout()
    }
  }

  /**
   * 更新 Token（用于 Token 刷新场景）
   */
  function updateToken(newToken: string) {
    token.value = newToken
    localStorage.setItem('access_token', newToken)
  }

  // 初始化时恢复用户信息
  initUserInfo()

  return {
    // State
    token,
    userInfo,
    currentEnvironment,

    // Computed
    isAuthenticated,
    isSupplier,
    isInternal,
    isPreviewEnv,

    // Actions
    login,
    logout,
    checkPermission,
    refreshUserInfo,
    updateToken
  }
})
