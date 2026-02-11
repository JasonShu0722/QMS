import request from '@/utils/request'
import type { LoginRequest, LoginResponse, User, PermissionCheckRequest } from '@/types/user'

/**
 * 认证相关 API
 */
export const authApi = {
  /**
   * 用户登录
   */
  login(data: LoginRequest): Promise<LoginResponse> {
    return request.post('/v1/auth/login', data)
  },

  /**
   * 用户注册
   */
  register(data: any): Promise<any> {
    return request.post('/v1/auth/register', data)
  },

  /**
   * 供应商模糊搜索
   */
  searchSuppliers(query: string): Promise<any[]> {
    return request.get('/v1/auth/suppliers/search', { params: { q: query } })
  },

  /**
   * 获取当前用户信息
   */
  getCurrentUser(): Promise<User> {
    return request.get('/v1/auth/me')
  },

  /**
   * 检查用户权限
   */
  checkPermission(modulePath: string, operation: string): Promise<boolean> {
    return request.post('/v1/auth/check-permission', {
      module_path: modulePath,
      operation
    } as PermissionCheckRequest)
  },

  /**
   * 获取图形验证码
   */
  getCaptcha(): Promise<{ captcha_id: string; captcha_image: string }> {
    return request.get('/v1/auth/captcha')
  },

  /**
   * 用户登出（可选，如果后端需要）
   */
  logout(): Promise<void> {
    return request.post('/v1/auth/logout')
  }
}
