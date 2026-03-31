import request from '@/utils/request'
import type {
  User,
  Permission,
  PermissionMatrixRow,
  PermissionMatrixColumn,
  OperationLog,
  OperationLogQuery,
  TodoTask,
  TaskStatistics,
  TaskReassignRequest,
  FeatureFlag,
  FeatureFlagUpdateRequest
} from '@/types/admin'

/**
 * 管理后台相关 API
 */
export const adminApi = {
  // ==================== 用户审核管理 ====================
  
  /**
   * 获取待审核用户列表
   */
  getPendingUsers(): Promise<User[]> {
    return request.get('/v1/admin/users/pending')
  },

  /**
   * 批准用户注册
   */
  approveUser(userId: number): Promise<void> {
    return request.post(`/v1/admin/users/${userId}/approve`)
  },

  /**
   * 拒绝用户注册
   */
  rejectUser(userId: number, reason: string): Promise<void> {
    return request.post(`/v1/admin/users/${userId}/reject`, { reason })
  },

  /**
   * 冻结用户账号
   */
  freezeUser(userId: number): Promise<void> {
    return request.post(`/v1/admin/users/${userId}/freeze`)
  },

  /**
   * 解冻用户账号
   */
  unfreezeUser(userId: number): Promise<void> {
    return request.post(`/v1/admin/users/${userId}/unfreeze`)
  },

  /**
   * 重置用户密码
   */
  resetUserPassword(userId: number): Promise<{ temporary_password: string }> {
    return request.post(`/v1/admin/users/${userId}/reset-password`)
  },

  // ==================== 权限管理 ====================

  /**
   * 获取权限矩阵
   */
  getPermissionMatrix(): Promise<{
    modules: PermissionMatrixColumn[]
    rows: PermissionMatrixRow[]
  }> {
    return request.get('/v1/admin/permissions/matrix')
  },

  /**
   * 授予权限
   */
  grantPermissions(data: {
    user_ids: number[]
    permissions: Array<{ module_path: string; operation_type: string }>
  }): Promise<void> {
    return request.put('/v1/admin/permissions/grant', data)
  },

  /**
   * 撤销权限
   */
  revokePermissions(data: {
    user_ids: number[]
    permissions: Array<{ module_path: string; operation_type: string }>
  }): Promise<void> {
    return request.put('/v1/admin/permissions/revoke', data)
  },

  /**
   * 获取用户权限详情
   */
  getUserPermissions(userId: number): Promise<Permission[]> {
    return request.get(`/v1/admin/permissions/users/${userId}`)
  },

  // ==================== 操作日志 ====================

  /**
   * 获取操作日志列表
   */
  getOperationLogs(query: OperationLogQuery): Promise<{
    logs: OperationLog[]
    total: number
    page: number
    page_size: number
  }> {
    return request.get('/v1/admin/operation-logs', { params: query })
  },

  /**
   * 获取操作日志详情
   */
  getOperationLogDetail(logId: number): Promise<OperationLog> {
    return request.get(`/v1/admin/operation-logs/${logId}`)
  },

  /**
   * 导出操作日志
   */
  exportOperationLogs(query: OperationLogQuery): Promise<Blob> {
    return request.get('/v1/admin/operation-logs/export', {
      params: query,
      responseType: 'blob'
    })
  },

  // ==================== 任务统计与监控 ====================

  /**
   * 获取任务统计数据
   */
  getTaskStatistics(): Promise<TaskStatistics> {
    return request.get('/v1/admin/tasks/statistics')
  },

  /**
   * 获取所有待办任务
   */
  getAllTasks(filters?: {
    urgency?: string
    department?: string
    user_id?: number
  }): Promise<TodoTask[]> {
    return request.get('/v1/admin/tasks', { params: filters })
  },

  /**
   * 批量转派任务
   */
  reassignTasks(data: TaskReassignRequest): Promise<void> {
    return request.post('/v1/admin/tasks/reassign', data)
  },

  // ==================== 功能开关管理 ====================

  /**
   * 获取所有功能开关
   */
  getFeatureFlags(environment?: 'stable' | 'preview'): Promise<FeatureFlag[]> {
    return request
      .get('/v1/admin/feature-flags', {
        params: environment ? { environment } : undefined
      })
      .then((response: any) => response.feature_flags || [])
  },

  /**
   * 更新功能开关
   */
  updateFeatureFlag(
    flagId: number,
    data: FeatureFlagUpdateRequest
  ): Promise<void> {
    return request.put(`/v1/admin/feature-flags/${flagId}`, data)
  },

  /**
   * 获取功能开关详情
   */
  getFeatureFlagDetail(flagId: number): Promise<FeatureFlag> {
    return request.get(`/v1/admin/feature-flags/${flagId}`)
  }
}
