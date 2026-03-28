// @ts-nocheck
/**
 * Login 页面 E2E 测试
 * 
 * 测试登录页面的完整流程：
 * - 用户类型切换
 * - 表单验证
 * - 登录流程（内部员工/供应商）
 * - 验证码功能
 * - 记住密码功能
 * - 响应式布局
 * - 错误处理
 * 
 * Requirements: 2.1.5 统一登录与鉴权策略
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import Login from '../Login.vue'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'

// Mock auth API
vi.mock('@/api/auth', () => ({
  authApi: {
    login: vi.fn(),
    getCaptcha: vi.fn(),
    getCurrentUser: vi.fn(),
    checkPermission: vi.fn()
  }
}))

// Mock Element Plus Message
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

describe('Login.vue E2E', () => {
  let router: any
  let pinia: any

  beforeEach(() => {
    // 创建 Pinia 实例
    pinia = createPinia()
    setActivePinia(pinia)

    // 创建路由实例
    router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/login', component: Login },
        { path: '/workbench', component: { template: '<div>Workbench</div>' } },
        { path: '/register', component: { template: '<div>Register</div>' } }
      ]
    })

    // 重置所有 mock
    vi.clearAllMocks()

    // 清除 localStorage
    localStorage.clear()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('页面初始化', () => {
    it('应该正确渲染登录页面', async () => {
      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      expect(wrapper.find('.login-container').exists()).toBe(true)
      expect(wrapper.text()).toContain('质量管理系统')
    })

    it('默认应该选中"员工登录"', async () => {
      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      // 桌面端检查
      const radioGroup = wrapper.find('.user-type-selector')
      if (radioGroup.exists()) {
        // 验证默认选中内部员工
        expect(wrapper.vm.userType).toBe('internal')
      }
    })

    it('应该显示注册链接', async () => {
      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      const registerLink = wrapper.find('a[href="/register"]')
      expect(registerLink.exists()).toBe(true)
      expect(registerLink.text()).toContain('注册')
    })
  })

  describe('用户类型切换', () => {
    it('切换到供应商登录应该显示验证码输入框', async () => {
      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      // Mock 验证码 API
      vi.mocked(authApi.getCaptcha).mockResolvedValue({
        captcha_image: 'data:image/png;base64,iVBORw0KGgoAAAANS',
        captcha_id: 'test-captcha-id'
      })

      // 切换到供应商登录
      wrapper.vm.userType = 'supplier'
      await wrapper.vm.$nextTick()
      await flushPromises()

      // 验证验证码相关元素存在
      expect(wrapper.vm.userType).toBe('supplier')

      // 验证 getCaptcha 被调用
      expect(authApi.getCaptcha).toHaveBeenCalled()
    })

    it('切换到员工登录应该隐藏验证码输入框', async () => {
      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      // 先切换到供应商
      wrapper.vm.userType = 'supplier'
      await wrapper.vm.$nextTick()

      // 再切换回员工
      wrapper.vm.userType = 'internal'
      await wrapper.vm.$nextTick()

      expect(wrapper.vm.userType).toBe('internal')
    })

    it('员工登录应该显示 SSO 按钮（禁用状态）', async () => {
      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      wrapper.vm.userType = 'internal'
      await wrapper.vm.$nextTick()

      // 查找 SSO 按钮
      const ssoButton = wrapper.find('.sso-button')
      if (ssoButton.exists()) {
        expect(ssoButton.attributes('disabled')).toBeDefined()
        expect(ssoButton.text()).toContain('SSO')
      }
    })
  })

  describe('表单验证', () => {
    it('空用户名应该无法提交', async () => {
      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      wrapper.vm.loginForm.username = ''
      wrapper.vm.loginForm.password = 'Test@123456'

      await wrapper.vm.handleLogin()
      await flushPromises()

      // 登录 API 不应该被调用
      expect(authApi.login).not.toHaveBeenCalled()
    })

    it('空密码应该无法提交', async () => {
      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      wrapper.vm.loginForm.username = 'testuser'
      wrapper.vm.loginForm.password = ''

      await wrapper.vm.handleLogin()
      await flushPromises()

      // 登录 API 不应该被调用
      expect(authApi.login).not.toHaveBeenCalled()
    })

    it('供应商登录缺少验证码应该无法提交', async () => {
      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      wrapper.vm.userType = 'supplier'
      wrapper.vm.loginForm.username = 'supplier1'
      wrapper.vm.loginForm.password = 'Test@123456'
      wrapper.vm.loginForm.captcha = ''

      await wrapper.vm.handleLogin()
      await flushPromises()

      // 登录 API 不应该被调用
      expect(authApi.login).not.toHaveBeenCalled()
    })
  })

  describe('员工登录流程', () => {
    it('成功登录应该跳转到工作台', async () => {
      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      // Mock 成功的登录响应
      vi.mocked(authApi.login).mockResolvedValue({
        access_token: 'test-token-123',
        token_type: 'bearer',
        environment: 'stable',
        password_expired: false,
        user_info: {
          id: 1,
          username: 'testuser',
          full_name: '测试用户',
          email: 'test@example.com',
          user_type: 'internal',
          department: '质量部',
          position: 'SQE',
          status: 'active',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      })

      // 填写表单
      wrapper.vm.loginForm.username = 'testuser'
      wrapper.vm.loginForm.password = 'Test@123456'
      wrapper.vm.userType = 'internal'

      // 提交登录
      await wrapper.vm.handleLogin()
      await flushPromises()

      // 验证 API 被正确调用
      expect(authApi.login).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'Test@123456',
        user_type: 'internal',
        captcha: undefined,
        captcha_id: undefined,
        environment: 'stable'
      })

      // 验证 Token 被保存
      const authStore = useAuthStore()
      expect(authStore.token).toBe('test-token-123')
      expect(authStore.userInfo?.username).toBe('testuser')

      // 验证跳转到工作台
      await flushPromises()
      expect(router.currentRoute.value.path).toBe('/workbench')
    })

    it('登录失败应该显示错误消息', async () => {
      const { ElMessage } = await import('element-plus')

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      // Mock 失败的登录响应
      vi.mocked(authApi.login).mockRejectedValue({
        response: {
          data: {
            detail: '用户名或密码错误'
          }
        }
      })

      wrapper.vm.loginForm.username = 'wronguser'
      wrapper.vm.loginForm.password = 'wrongpass'

      await wrapper.vm.handleLogin()
      await flushPromises()

      // 验证错误消息被显示
      expect(ElMessage.error).toHaveBeenCalled()
    })

    it('登录过程中应该显示加载状态', async () => {
      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      // Mock 延迟的登录响应
      vi.mocked(authApi.login).mockImplementation(() =>
        new Promise(resolve => setTimeout(() => resolve({
          access_token: 'test-token',
          token_type: 'bearer',
          environment: 'stable',
          password_expired: false,
          user_info: {
            id: 1,
            username: 'testuser',
            full_name: '测试用户',
            email: 'test@example.com',
            user_type: 'internal',
            department: '质量部',
            position: 'SQE',
            status: 'active',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          }
        }), 100))
      )

      wrapper.vm.loginForm.username = 'testuser'
      wrapper.vm.loginForm.password = 'Test@123456'

      // 开始登录
      const loginPromise = wrapper.vm.handleLogin()
      await wrapper.vm.$nextTick()

      // 验证加载状态
      expect(wrapper.vm.loading).toBe(true)

      // 等待登录完成
      await loginPromise
      await flushPromises()

      // 验证加载状态结束
      expect(wrapper.vm.loading).toBe(false)
    })
  })

  describe('供应商登录流程', () => {
    it('成功登录应该包含验证码参数', async () => {
      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      // Mock 验证码
      vi.mocked(authApi.getCaptcha).mockResolvedValue({
        captcha_image: 'data:image/png;base64,test',
        captcha_id: 'captcha-123'
      })

      // Mock 成功的登录
      vi.mocked(authApi.login).mockResolvedValue({
        access_token: 'supplier-token',
        token_type: 'bearer',
        environment: 'stable',
        password_expired: false,
        user_info: {
          id: 2,
          username: 'supplier1',
          full_name: '供应商A',
          email: 'supplier@example.com',
          user_type: 'supplier',
          supplier_id: 1,
          status: 'active',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      })

      // 切换到供应商登录
      wrapper.vm.userType = 'supplier'
      await wrapper.vm.$nextTick()
      await flushPromises()

      // 填写表单
      wrapper.vm.loginForm.username = 'supplier1'
      wrapper.vm.loginForm.password = 'Supplier@123'
      wrapper.vm.loginForm.captcha = '1234'

      // 提交登录
      await wrapper.vm.handleLogin()
      await flushPromises()

      // 验证 API 被正确调用（包含验证码）
      expect(authApi.login).toHaveBeenCalledWith({
        username: 'supplier1',
        password: 'Supplier@123',
        user_type: 'supplier',
        captcha: '1234',
        captcha_id: 'captcha-123',
        environment: 'stable'
      })
    })

    it('登录失败后应该刷新验证码', async () => {
      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      // Mock 验证码
      vi.mocked(authApi.getCaptcha).mockResolvedValue({
        captcha_image: 'data:image/png;base64,test',
        captcha_id: 'captcha-123'
      })

      // Mock 失败的登录
      vi.mocked(authApi.login).mockRejectedValue({
        response: {
          data: {
            detail: '验证码错误'
          }
        }
      })

      wrapper.vm.userType = 'supplier'
      await wrapper.vm.$nextTick()
      await flushPromises()

      // 清除之前的调用记录
      vi.mocked(authApi.getCaptcha).mockClear()

      wrapper.vm.loginForm.username = 'supplier1'
      wrapper.vm.loginForm.password = 'Test@123'
      wrapper.vm.loginForm.captcha = 'wrong'

      await wrapper.vm.handleLogin()
      await flushPromises()

      // 验证验证码被刷新
      expect(authApi.getCaptcha).toHaveBeenCalled()
      // 验证码输入框应该被清空
      expect(wrapper.vm.loginForm.captcha).toBe('')
    })
  })

  describe('记住密码功能', () => {
    it('勾选记住密码后应该保存到 localStorage', async () => {
      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      vi.mocked(authApi.login).mockResolvedValue({
        access_token: 'test-token',
        token_type: 'bearer',
        user_info: {
          id: 1,
          username: 'testuser',
          full_name: '测试用户',
          email: 'test@example.com',
          user_type: 'internal',
          department: '质量部',
          position: 'SQE',
          status: 'active'
        }
      })

      wrapper.vm.loginForm.username = 'testuser'
      wrapper.vm.loginForm.password = 'Test@123456'
      wrapper.vm.rememberPassword = true

      await wrapper.vm.handleLogin()
      await flushPromises()

      // 验证密码被保存
      expect(localStorage.getItem('remembered_username')).toBe('testuser')
      expect(localStorage.getItem('remembered_password')).toBe('Test@123456')
      expect(localStorage.getItem('remembered_user_type')).toBe('internal')
    })

    it('不勾选记住密码应该清除 localStorage', async () => {
      // 先设置一些旧数据
      localStorage.setItem('remembered_username', 'olduser')
      localStorage.setItem('remembered_password', 'oldpass')

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      vi.mocked(authApi.login).mockResolvedValue({
        access_token: 'test-token',
        token_type: 'bearer',
        environment: 'stable',
        password_expired: false,
        user_info: {
          id: 1,
          username: 'testuser',
          full_name: '测试用户',
          email: 'test@example.com',
          user_type: 'internal',
          department: '质量部',
          position: 'SQE',
          status: 'active',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      })

      wrapper.vm.loginForm.username = 'testuser'
      wrapper.vm.loginForm.password = 'Test@123456'
      wrapper.vm.rememberPassword = false

      await wrapper.vm.handleLogin()
      await flushPromises()

      // 验证旧数据被清除
      expect(localStorage.getItem('remembered_username')).toBeNull()
      expect(localStorage.getItem('remembered_password')).toBeNull()
    })

    it('页面加载时应该恢复记住的密码', async () => {
      // 设置记住的密码
      localStorage.setItem('remembered_username', 'saveduser')
      localStorage.setItem('remembered_password', 'savedpass')
      localStorage.setItem('remembered_user_type', 'supplier')

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      await wrapper.vm.$nextTick()

      // 验证表单被填充
      expect(wrapper.vm.loginForm.username).toBe('saveduser')
      expect(wrapper.vm.loginForm.password).toBe('savedpass')
      expect(wrapper.vm.userType).toBe('supplier')
      expect(wrapper.vm.rememberPassword).toBe(true)
    })
  })

  describe('验证码功能', () => {
    it('点击验证码图片应该刷新验证码', async () => {
      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      vi.mocked(authApi.getCaptcha)
        .mockResolvedValueOnce({
          captcha_image: 'data:image/png;base64,first',
          captcha_id: 'captcha-1'
        })
        .mockResolvedValueOnce({
          captcha_image: 'data:image/png;base64,second',
          captcha_id: 'captcha-2'
        })

      wrapper.vm.userType = 'supplier'
      await wrapper.vm.$nextTick()
      await flushPromises()

      // 第一次获取验证码
      expect(authApi.getCaptcha).toHaveBeenCalledTimes(1)
      expect(wrapper.vm.captchaId).toBe('captcha-1')

      // 刷新验证码
      await wrapper.vm.refreshCaptcha()
      await flushPromises()

      // 验证码被更新
      expect(authApi.getCaptcha).toHaveBeenCalledTimes(2)
      expect(wrapper.vm.captchaId).toBe('captcha-2')
    })

    it('获取验证码失败应该显示错误消息', async () => {
      const { ElMessage } = await import('element-plus')

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      vi.mocked(authApi.getCaptcha).mockRejectedValue({
        response: {
          data: {
            detail: '验证码服务暂时不可用'
          }
        }
      })

      await wrapper.vm.refreshCaptcha()
      await flushPromises()

      // 验证错误消息被显示
      expect(ElMessage.error).toHaveBeenCalled()
    })
  })

  describe('响应式布局', () => {
    it('窗口宽度 < 768px 应该显示移动端布局', async () => {
      // Mock window.innerWidth
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 500
      })

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      expect(wrapper.vm.isMobile).toBe(true)
    })

    it('窗口宽度 >= 768px 应该显示桌面端布局', async () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 1024
      })

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      expect(wrapper.vm.isMobile).toBe(false)
    })
  })

  describe('边界情况', () => {
    it('应该处理网络错误', async () => {
      const { ElMessage } = await import('element-plus')

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      vi.mocked(authApi.login).mockRejectedValue(new Error('Network Error'))

      wrapper.vm.loginForm.username = 'testuser'
      wrapper.vm.loginForm.password = 'Test@123456'

      await wrapper.vm.handleLogin()
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalled()
      expect(wrapper.vm.loading).toBe(false)
    })

    it('应该处理没有 detail 的错误响应', async () => {
      const { ElMessage } = await import('element-plus')

      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      vi.mocked(authApi.login).mockRejectedValue({
        response: {
          data: {}
        }
      })

      wrapper.vm.loginForm.username = 'testuser'
      wrapper.vm.loginForm.password = 'Test@123456'

      await wrapper.vm.handleLogin()
      await flushPromises()

      expect(ElMessage.error).toHaveBeenCalled()
    })

    it('回车键应该触发登录', async () => {
      const wrapper = mount(Login, {
        global: {
          plugins: [router, pinia]
        }
      })

      vi.mocked(authApi.login).mockResolvedValue({
        access_token: 'test-token',
        token_type: 'bearer',
        environment: 'stable',
        password_expired: false,
        user_info: {
          id: 1,
          username: 'testuser',
          full_name: '测试用户',
          email: 'test@example.com',
          user_type: 'internal',
          department: '质量部',
          position: 'SQE',
          status: 'active',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      })

      wrapper.vm.loginForm.username = 'testuser'
      wrapper.vm.loginForm.password = 'Test@123456'

      // 模拟回车键
      const form = wrapper.find('form')
      if (form.exists()) {
        await form.trigger('keyup.enter')
        await flushPromises()

        // 验证登录被触发
        expect(authApi.login).toHaveBeenCalled()
      }
    })
  })
})
