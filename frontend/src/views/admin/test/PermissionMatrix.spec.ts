import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, shallowMount } from '@vue/test-utils'
import PermissionMatrix from '../PermissionMatrix.vue'

const adminApiMocks = vi.hoisted(() => ({
  getPermissionMatrixMock: vi.fn(),
  grantPermissionsMock: vi.fn(),
  revokePermissionsMock: vi.fn()
}))

const messageMocks = vi.hoisted(() => ({
  successMock: vi.fn(),
  errorMock: vi.fn(),
  infoMock: vi.fn()
}))

vi.mock('@/api/admin', () => ({
  adminApi: {
    getPermissionMatrix: adminApiMocks.getPermissionMatrixMock,
    grantPermissions: adminApiMocks.grantPermissionsMock,
    revokePermissions: adminApiMocks.revokePermissionsMock
  }
}))

vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: messageMocks.successMock,
      error: messageMocks.errorMock,
      info: messageMocks.infoMock
    }
  }
})

function mountPermissionMatrix() {
  return shallowMount(PermissionMatrix, {
    global: {
      stubs: {
        'el-card': { template: '<div><slot name="header" /><slot /></div>' },
        'el-button': { template: '<button><slot /></button>' },
        'el-icon': { template: '<span><slot /></span>' },
        'el-checkbox': { template: '<input type="checkbox" />' },
        'el-tag': { template: '<span><slot /></span>' },
        'el-alert': { template: '<div><slot name="title" /></div>' }
      }
    }
  })
}

describe('PermissionMatrix.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    adminApiMocks.getPermissionMatrixMock.mockResolvedValue({
      modules: [
        {
          module_path: 'foundation.users',
          module_name: 'User Governance',
          operations: ['read', 'update']
        }
      ],
      rows: [
        {
          user: {
            id: 8,
            username: 'platform-admin',
            full_name: 'Platform Admin',
            email: 'admin@example.com',
            user_type: 'internal',
            status: 'active',
            is_platform_admin: true,
            created_at: '2026-03-31T00:00:00Z',
            updated_at: '2026-03-31T00:00:00Z'
          },
          permissions: {
            'foundation.users.read': true,
            'foundation.users.update': false
          }
        }
      ]
    })
    adminApiMocks.grantPermissionsMock.mockResolvedValue(undefined)
    adminApiMocks.revokePermissionsMock.mockResolvedValue(undefined)
  })

  it('loads modules and rows from the unified matrix contract', async () => {
    const wrapper = mountPermissionMatrix()
    await flushPromises()

    expect(adminApiMocks.getPermissionMatrixMock).toHaveBeenCalledTimes(1)
    expect((wrapper.vm as any).modules).toHaveLength(1)
    expect((wrapper.vm as any).permissionRows).toHaveLength(1)
    expect((wrapper.vm as any).permissionRows[0].permissions['foundation.users.read']).toBe(true)
  })

  it('groups grant and revoke changes by user when saving', async () => {
    const wrapper = mountPermissionMatrix()
    await flushPromises()

    ;(wrapper.vm as any).handlePermissionChange(8, 'foundation.users', 'read', false)
    ;(wrapper.vm as any).handlePermissionChange(8, 'foundation.users', 'update', true)
    await (wrapper.vm as any).saveAllChanges()

    expect(adminApiMocks.grantPermissionsMock).toHaveBeenCalledWith({
      user_ids: [8],
      permissions: [{ module_path: 'foundation.users', operation_type: 'update' }]
    })
    expect(adminApiMocks.revokePermissionsMock).toHaveBeenCalledWith({
      user_ids: [8],
      permissions: [{ module_path: 'foundation.users', operation_type: 'read' }]
    })
    expect(messageMocks.successMock).toHaveBeenCalled()
  })
})
