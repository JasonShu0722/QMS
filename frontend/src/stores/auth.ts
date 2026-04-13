import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User } from '@/types/user'
import { detectEntryEnvironment, normalizeEntryEnvironment, type EntryEnvironment } from '@/utils/environment'

/**
 * Authentication store
 *
 * Environment rules:
 * - On deployed domains, runtime hostname is the source of truth.
 * - In local development, `current_environment` in localStorage is used.
 * - Login requests still send the selected business environment explicitly.
 */
export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const userInfo = ref<User | null>(null)
  const currentEnvironment = ref<EntryEnvironment>(detectEntryEnvironment())

  const isAuthenticated = computed(() => !!token.value)
  const isSupplier = computed(() => userInfo.value?.user_type === 'supplier')
  const isInternal = computed(() => userInfo.value?.user_type === 'internal')
  const isPreviewEnv = computed(() => currentEnvironment.value === 'preview')
  const isPlatformAdmin = computed(() => !!userInfo.value?.is_platform_admin)
  const allowedEnvironments = computed(() => {
    const raw = userInfo.value?.allowed_environments?.split(',').map((item) => item.trim()).filter(Boolean)
    return raw && raw.length > 0 ? raw : ['stable']
  })

  function initUserInfo() {
    const storedUserInfo = localStorage.getItem('user_info')
    if (!storedUserInfo) {
      return
    }

    try {
      userInfo.value = JSON.parse(storedUserInfo)
    } catch (error) {
      console.error('Failed to parse user info from localStorage:', error)
      logout()
    }
  }

  async function login(
    username: string,
    password: string,
    userType: 'internal' | 'supplier',
    captcha?: string,
    captchaId?: string,
    environment: EntryEnvironment = 'stable'
  ): Promise<void> {
    const { authApi } = await import('@/api/auth')

    const response = await authApi.login({
      username,
      password,
      user_type: userType,
      captcha,
      captcha_id: captchaId,
      environment
    })

    token.value = response.access_token
    userInfo.value = response.user_info
    currentEnvironment.value = normalizeEntryEnvironment(environment)

    localStorage.setItem('access_token', response.access_token)
    localStorage.setItem(
      'user_info',
      JSON.stringify({
        ...response.user_info,
        allowed_environments: response.allowed_environments.join(',')
      })
    )
    localStorage.setItem('current_environment', currentEnvironment.value)

    const { useFeatureFlagStore } = await import('@/stores/featureFlag')
    const featureFlagStore = useFeatureFlagStore()
    await featureFlagStore.loadFeatureFlags(true)
  }

  function logout() {
    token.value = null
    userInfo.value = null
    currentEnvironment.value = detectEntryEnvironment()
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_info')
    localStorage.removeItem('current_environment')
  }

  async function checkPermission(
    modulePath: string,
    operation: 'create' | 'read' | 'update' | 'delete' | 'export'
  ): Promise<boolean> {
    if (!isAuthenticated.value || !userInfo.value) {
      return false
    }

    try {
      const { authApi } = await import('@/api/auth')
      return await authApi.checkPermission(modulePath, operation)
    } catch (error) {
      console.error('Permission check failed:', error)
      return false
    }
  }

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
      logout()
    }
  }

  function updateToken(newToken: string) {
    token.value = newToken
    localStorage.setItem('access_token', newToken)
  }

  initUserInfo()

  return {
    token,
    userInfo,
    currentEnvironment,
    isAuthenticated,
    isSupplier,
    isInternal,
    isPreviewEnv,
    isPlatformAdmin,
    allowedEnvironments,
    login,
    logout,
    checkPermission,
    refreshUserInfo,
    updateToken
  }
})
