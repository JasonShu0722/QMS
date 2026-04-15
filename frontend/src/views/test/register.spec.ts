// @ts-nocheck
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import ElementPlus from 'element-plus'
import Register from '../Register.vue'
import { authApi } from '@/api/auth'

vi.mock('@/api/auth', () => ({
  authApi: {
    register: vi.fn(),
    searchSuppliers: vi.fn()
  }
}))

vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
      info: vi.fn()
    }
  }
})

describe('Register.vue', () => {
  let router: any
  let pinia: any

  const mountRegister = () => mount(Register, {
    global: {
      plugins: [router, pinia, ElementPlus],
      stubs: {
        SupplierSearch: {
          template: '<div class="supplier-search-stub">SupplierSearch</div>',
          props: ['modelValue', 'supplierName'],
          emits: ['update:modelValue', 'update:supplierName']
        }
      }
    }
  })

  beforeEach(async () => {
    pinia = createPinia()
    setActivePinia(pinia)

    router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/register', component: Register },
        { path: '/login', component: { template: '<div>Login</div>' } }
      ]
    })

    vi.clearAllMocks()

    await router.push('/register')
    await router.isReady()
  })

  it('renders the register page with shared visual entry points', () => {
    const wrapper = mountRegister()

    expect(wrapper.find('.register-container').exists()).toBe(true)
    expect(wrapper.find('.register-panel-shell').exists()).toBe(true)
    expect(wrapper.text()).toContain('用户注册')
    expect(wrapper.text()).toContain('统一账号申请')
  })

  it('submits internal registration payload and returns to login', async () => {
    vi.mocked(authApi.register).mockResolvedValue({ message: '注册成功' })

    const wrapper = mountRegister()
    wrapper.vm.registerForm.username = 'internal_user'
    wrapper.vm.registerForm.full_name = '测试员工'
    wrapper.vm.registerForm.password = 'Test@123456'
    wrapper.vm.registerForm.confirmPassword = 'Test@123456'
    wrapper.vm.registerForm.email = 'internal@example.com'
    wrapper.vm.registerForm.phone = '13800138000'
    wrapper.vm.registerForm.department = '质量部'
    wrapper.vm.registerForm.position = '质量工程师'

    await wrapper.vm.$nextTick()
    await wrapper.vm.handleRegister()
    await flushPromises()

    expect(authApi.register).toHaveBeenCalledWith({
      username: 'internal_user',
      password: 'Test@123456',
      full_name: '测试员工',
      email: 'internal@example.com',
      phone: '13800138000',
      user_type: 'internal',
      position: '质量工程师',
      department: '质量部'
    })
    expect(router.currentRoute.value.path).toBe('/login')
  })

  it('switches to supplier registration and uses supplier payload', async () => {
    vi.mocked(authApi.register).mockResolvedValue({ message: '注册成功' })

    const wrapper = mountRegister()
    wrapper.vm.registerForm.department = '质量部'
    wrapper.vm.userType = 'supplier'

    await wrapper.vm.$nextTick()

    expect(wrapper.vm.registerForm.department).toBe('')
    expect(wrapper.find('.supplier-search-stub').exists()).toBe(true)

    wrapper.vm.registerForm.username = 'supplier_user'
    wrapper.vm.registerForm.full_name = '供应商联系人'
    wrapper.vm.registerForm.password = 'Supplier@123'
    wrapper.vm.registerForm.confirmPassword = 'Supplier@123'
    wrapper.vm.registerForm.email = 'supplier@example.com'
    wrapper.vm.registerForm.phone = '13900139000'
    wrapper.vm.registerForm.supplier_id = 9
    wrapper.vm.registerForm.position = '质量窗口'

    await wrapper.vm.handleRegister()
    await flushPromises()

    expect(authApi.register).toHaveBeenCalledWith({
      username: 'supplier_user',
      password: 'Supplier@123',
      full_name: '供应商联系人',
      email: 'supplier@example.com',
      phone: '13900139000',
      user_type: 'supplier',
      position: '质量窗口',
      supplier_id: 9
    })
  })

  it('blocks submission when required fields are incomplete', async () => {
    const wrapper = mountRegister()
    wrapper.vm.registerForm.username = ''
    wrapper.vm.registerForm.full_name = '测试员工'
    wrapper.vm.registerForm.password = 'Test@123456'
    wrapper.vm.registerForm.confirmPassword = 'Test@123456'
    wrapper.vm.registerForm.email = 'internal@example.com'
    wrapper.vm.registerForm.department = '质量部'

    await wrapper.vm.handleRegister()
    await flushPromises()

    expect(authApi.register).not.toHaveBeenCalled()
  })
})
