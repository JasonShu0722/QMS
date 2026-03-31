import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'

const loginMock = vi.fn()
const getCurrentUserMock = vi.fn()
const checkPermissionMock = vi.fn()
const loadFeatureFlagsMock = vi.fn()

vi.mock('@/api/auth', () => ({
  authApi: {
    login: loginMock,
    getCurrentUser: getCurrentUserMock,
    checkPermission: checkPermissionMock
  }
}))

vi.mock('@/stores/featureFlag', () => ({
  useFeatureFlagStore: () => ({
    loadFeatureFlags: loadFeatureFlagsMock
  })
}))

type StorageState = Record<string, string>

function installStorage(initialState: StorageState = {}) {
  const state: StorageState = { ...initialState }

  Object.defineProperty(window, 'localStorage', {
    configurable: true,
    value: {
      getItem: vi.fn((key: string) => state[key] ?? null),
      setItem: vi.fn((key: string, value: string) => {
        state[key] = String(value)
      }),
      removeItem: vi.fn((key: string) => {
        delete state[key]
      }),
      clear: vi.fn(() => {
        Object.keys(state).forEach((key) => delete state[key])
      })
    }
  })

  return state
}

function installLocation(hostname: string, href: string) {
  Object.defineProperty(window, 'location', {
    configurable: true,
    value: {
      hostname,
      href,
      reload: vi.fn()
    }
  })
}

describe('auth store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    installStorage()
    installLocation('localhost', 'http://localhost:5173/login')
  })

  it('hydrates preview environment from local storage on localhost', () => {
    installStorage({ current_environment: 'preview' })

    const store = useAuthStore()

    expect(store.currentEnvironment).toBe('preview')
    expect(store.allowedEnvironments).toEqual(['stable'])
  })

  it('persists normalized session data after login', async () => {
    loginMock.mockResolvedValue({
      access_token: 'token-123',
      token_type: 'bearer',
      environment: 'preview',
      allowed_environments: ['stable', 'preview'],
      password_expired: false,
      user_info: {
        id: 7,
        username: 'platform-admin',
        full_name: 'Platform Admin',
        email: 'admin@example.com',
        user_type: 'internal',
        status: 'active',
        allowed_environments: 'stable,preview',
        is_platform_admin: true,
        created_at: '2026-03-31T00:00:00Z',
        updated_at: '2026-03-31T00:00:00Z'
      }
    })

    const store = useAuthStore()
    await store.login('platform-admin', 'Secret123!', 'internal', undefined, undefined, 'preview')

    expect(store.token).toBe('token-123')
    expect(store.currentEnvironment).toBe('preview')
    expect(store.isPlatformAdmin).toBe(true)
    expect(store.allowedEnvironments).toEqual(['stable', 'preview'])
    expect(window.localStorage.setItem).toHaveBeenCalledWith('access_token', 'token-123')
    expect(window.localStorage.setItem).toHaveBeenCalledWith('current_environment', 'preview')
    expect(loadFeatureFlagsMock).toHaveBeenCalledWith(true)
  })

  it('refreshes user info and preserves normalized payload fields', async () => {
    installStorage({
      access_token: 'token-abc',
      user_info: JSON.stringify({
        id: 1,
        username: 'supplier_user',
        full_name: 'Supplier User',
        email: 'supplier@example.com',
        user_type: 'supplier',
        status: 'active',
        allowed_environments: 'stable',
        created_at: '2026-03-31T00:00:00Z',
        updated_at: '2026-03-31T00:00:00Z'
      })
    })

    getCurrentUserMock.mockResolvedValue({
      id: 1,
      username: 'supplier_user',
      full_name: 'Supplier User',
      email: 'supplier@example.com',
      user_type: 'supplier',
      status: 'active',
      supplier_id: 5,
      supplier_name: 'Northwind Components',
      signature_image_path: '/uploads/signatures/supplier_user.png',
      allowed_environments: 'stable,preview',
      created_at: '2026-03-31T00:00:00Z',
      updated_at: '2026-03-31T00:00:00Z'
    })

    const store = useAuthStore()
    await store.refreshUserInfo()

    expect(store.userInfo?.supplier_name).toBe('Northwind Components')
    expect(store.userInfo?.signature_image_path).toBe('/uploads/signatures/supplier_user.png')
    expect(store.allowedEnvironments).toEqual(['stable', 'preview'])
  })
})
