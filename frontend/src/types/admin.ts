/**
 * 管理后台相关类型定义
 */

import type { User } from './user'

// Re-export for external use
export type { User, UserStatus } from './user'

/**
 * 操作类型
 */
export type OperationType = 'create' | 'read' | 'update' | 'delete' | 'export'

/**
 * 权限配置项
 */
export interface Permission {
  id: number
  user_id: number
  module_path: string
  operation_type: OperationType
  is_granted: boolean
  created_at: string
  updated_at: string
}

/**
 * 权限矩阵行（用户维度）
 */
export interface PermissionMatrixRow {
  user: User
  permissions: Record<string, boolean> // key: "module_path.operation_type"
}

/**
 * 权限矩阵列（功能-操作维度）
 */
export interface PermissionMatrixColumn {
  module_path: string
  module_name: string
  operations: OperationType[]
}

/**
 * 操作日志
 */
export interface OperationLog {
  id: number
  user_id: number
  user_name: string
  operation_type: string
  target_type: string
  target_id?: number
  before_snapshot?: string
  after_snapshot?: string
  description?: string
  ip_address: string
  user_agent: string
  created_at: string
}

/**
 * 操作日志查询参数
 */
export interface OperationLogQuery {
  user_id?: number
  operation_type?: string
  target_type?: string
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}

/**
 * 待办任务
 */
export interface TodoTask {
  id: string
  task_type: string
  task_id: number
  title: string
  description?: string
  deadline: string
  remaining_hours: number
  urgency: 'overdue' | 'urgent' | 'normal'
  color: 'red' | 'yellow' | 'green'
  link: string
  handler_id: number
  handler_name: string
}

/**
 * 任务统计数据
 */
export interface TaskStatistics {
  total_tasks: number
  overdue_tasks: number
  urgent_tasks: number
  normal_tasks: number
  by_department: Record<string, number>
  by_user: Record<string, number>
}

/**
 * 任务转派请求
 */
export interface TaskReassignRequest {
  from_user_id: number
  to_user_id: number
  task_ids: string[]
}

/**
 * 功能开关
 */
export interface FeatureFlag {
  id: number
  feature_key: string
  feature_name: string
  description: string
  is_enabled: boolean
  scope: 'global' | 'whitelist'
  whitelist_user_ids: number[]
  whitelist_supplier_ids: number[]
  environment: 'stable' | 'preview'
  created_at: string
  updated_at: string
  created_by?: number
}

/**
 * 功能开关更新请求
 */
export interface FeatureFlagUpdateRequest {
  is_enabled: boolean
  scope?: 'global' | 'whitelist'
  whitelist_user_ids?: number[]
  whitelist_supplier_ids?: number[]
  environment?: 'stable' | 'preview'
}

/**
 * 用户审核操作
 */
export interface UserApprovalRequest {
  user_id: number
  action: 'approve' | 'reject'
  reason?: string
}
