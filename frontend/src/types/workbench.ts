/**
 * 工作台相关类型定义
 */

/**
 * 任务紧急程度
 */
export type TaskUrgency = 'overdue' | 'urgent' | 'normal'

/**
 * 任务颜色
 */
export type TaskColor = 'red' | 'yellow' | 'green'

/**
 * 待办任务
 */
export interface TodoTask {
  task_type: string          // 任务类型（如"8D报告审核"）
  task_id: string | number   // 单据编号
  deadline: string           // 截止时间
  remaining_hours: number    // 剩余处理时间（小时）
  urgency: TaskUrgency       // 紧急程度
  color: TaskColor           // 颜色标识
  link: string               // 跳转链接
  title?: string             // 任务标题
  description?: string       // 任务描述
}

/**
 * 指标数据
 */
export interface Metric {
  key: string                // 指标唯一标识
  name: string               // 指标名称
  value: string | number     // 指标值
  status: 'good' | 'warning' | 'danger'  // 状态
  achievement?: number       // 达成率（百分比）
  unit?: string              // 单位
}

/**
 * 供应商绩效状态
 */
export interface PerformanceStatus {
  grade: 'A' | 'B' | 'C' | 'D'  // 绩效等级
  score: number                  // 当前得分
  deduction_this_month: number   // 本月扣分
}

/**
 * 内部员工工作台数据
 */
export interface InternalDashboard {
  user_info: any              // 用户信息
  metrics: Metric[]           // 指标监控
  todos: TodoTask[]           // 待办任务
  notifications: number       // 未读消息数量
}

/**
 * 供应商工作台数据
 */
export interface SupplierDashboard {
  user_info: any                        // 用户信息
  performance_status: PerformanceStatus // 绩效状态
  action_required_tasks: TodoTask[]     // 需要行动的任务
}

/**
 * 工作台数据（联合类型）
 */
export type DashboardData = InternalDashboard | SupplierDashboard

/**
 * 修改密码请求
 */
export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}

/**
 * 电子签名上传响应
 */
export interface SignatureUploadResponse {
  signature_image_path: string
  message: string
}
