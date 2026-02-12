/**
 * 通知相关类型定义
 */

/**
 * 通知类型
 */
export type NotificationType = 'workflow' | 'system' | 'alert'

/**
 * 通知对象
 */
export interface Notification {
  id: number
  user_id: number
  title: string
  content: string
  type: NotificationType
  link?: string
  is_read: boolean
  read_at?: string
  created_at: string
}

/**
 * 通知类型标签映射
 */
export const NotificationTypeLabels: Record<NotificationType, string> = {
  workflow: '流程异常',
  system: '系统提醒',
  alert: '预警通知'
}

/**
 * 通知类型颜色映射
 */
export const NotificationTypeColors: Record<NotificationType, string> = {
  workflow: 'warning',
  system: 'info',
  alert: 'danger'
}

/**
 * 未读消息数量响应
 */
export interface UnreadCountResponse {
  unread_count: number
}

/**
 * 通知列表响应
 */
export interface NotificationListResponse {
  notifications: Notification[]
  total: number
  page: number
  page_size: number
}

/**
 * 标记已读请求
 */
export interface MarkReadRequest {
  notification_id?: number  // 单条消息ID（可选）
}
