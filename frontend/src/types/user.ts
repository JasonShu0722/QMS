/**
 * 用户类型定义
 */
export type UserType = 'internal' | 'supplier'

/**
 * 用户状态
 */
export type UserStatus = 'pending' | 'active' | 'frozen' | 'rejected'

/**
 * 用户信息接口
 */
export interface User {
  id: number
  username: string
  full_name: string
  email: string
  phone?: string
  user_type: UserType
  status: UserStatus
  
  // 内部员工字段
  department?: string
  position?: string
  role_id?: number
  
  // 供应商字段
  supplier_id?: number
  supplier_name?: string
  
  // 电子签名
  signature_image_path?: string
  
  // 审计字段
  created_at: string
  updated_at: string
  last_login_at?: string
}

/**
 * 登录请求参数
 */
export interface LoginRequest {
  username: string
  password: string
  user_type: UserType
  captcha?: string
  captcha_id?: string
}

/**
 * 登录响应
 */
export interface LoginResponse {
  access_token: string
  token_type: string
  user_info: User
}

/**
 * 权限检查请求
 */
export interface PermissionCheckRequest {
  module_path: string
  operation: 'create' | 'read' | 'update' | 'delete' | 'export'
}
