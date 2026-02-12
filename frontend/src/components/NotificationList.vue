<template>
  <div class="notification-list">
    <!-- 顶部操作栏 -->
    <div class="notification-header">
      <!-- 消息类型筛选 -->
      <el-select
        v-model="selectedType"
        placeholder="全部消息"
        clearable
        @change="handleTypeChange"
        class="type-filter"
      >
        <el-option label="全部消息" :value="undefined" />
        <el-option
          v-for="(label, type) in NotificationTypeLabels"
          :key="type"
          :label="label"
          :value="type"
        />
      </el-select>

      <!-- 一键标记全部已读 -->
      <el-button
        type="primary"
        size="small"
        :disabled="notifications.length === 0 || !hasUnread"
        @click="handleMarkAllRead"
        :loading="markingAllRead"
      >
        全部已读
      </el-button>
    </div>

    <!-- 通知列表 -->
    <div class="notification-content" v-loading="loading">
      <!-- 空状态 -->
      <el-empty
        v-if="notifications.length === 0 && !loading"
        description="暂无通知消息"
        :image-size="100"
      />

      <!-- 消息列表 -->
      <div v-else class="notification-items">
        <div
          v-for="notification in notifications"
          :key="notification.id"
          class="notification-item"
          :class="{ 'is-read': notification.is_read }"
          @click="handleNotificationClick(notification)"
        >
          <!-- 未读标识 -->
          <div class="unread-dot" v-if="!notification.is_read"></div>

          <!-- 消息内容 -->
          <div class="notification-body">
            <!-- 消息类型标签 -->
            <el-tag
              :type="NotificationTypeColors[notification.type]"
              size="small"
              class="type-tag"
            >
              {{ NotificationTypeLabels[notification.type] }}
            </el-tag>

            <!-- 消息标题 -->
            <div class="notification-title">
              {{ notification.title }}
            </div>

            <!-- 消息内容 -->
            <div class="notification-text">
              {{ notification.content }}
            </div>

            <!-- 消息时间 -->
            <div class="notification-time">
              {{ formatTime(notification.created_at) }}
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="notification-actions">
            <el-button
              v-if="!notification.is_read"
              type="primary"
              size="small"
              text
              @click.stop="handleMarkRead(notification.id)"
            >
              标记已读
            </el-button>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div class="notification-pagination" v-if="total > pageSize">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          small
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { notificationApi } from '@/api/notification'
import type { Notification, NotificationType } from '@/types/notification'
import { NotificationTypeLabels, NotificationTypeColors } from '@/types/notification'

/**
 * 定义事件
 */
const emit = defineEmits<{
  notificationRead: []
  allRead: []
}>()

/**
 * 路由实例
 */
const router = useRouter()

/**
 * 通知列表
 */
const notifications = ref<Notification[]>([])

/**
 * 加载状态
 */
const loading = ref<boolean>(false)

/**
 * 标记全部已读加载状态
 */
const markingAllRead = ref<boolean>(false)

/**
 * 选中的消息类型
 */
const selectedType = ref<NotificationType | undefined>(undefined)

/**
 * 当前页码
 */
const currentPage = ref<number>(1)

/**
 * 每页数量
 */
const pageSize = ref<number>(20)

/**
 * 总数量
 */
const total = ref<number>(0)

/**
 * 是否有未读消息
 */
const hasUnread = computed(() => {
  return notifications.value.some(n => !n.is_read)
})

/**
 * 获取通知列表
 */
const fetchNotifications = async () => {
  loading.value = true
  try {
    const response = await notificationApi.getNotifications(
      selectedType.value,
      currentPage.value,
      pageSize.value
    )
    notifications.value = response.notifications
    total.value = response.total
  } catch (error) {
    console.error('Failed to fetch notifications:', error)
    ElMessage.error('获取通知列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 处理消息类型筛选变化
 */
const handleTypeChange = () => {
  currentPage.value = 1
  fetchNotifications()
}

/**
 * 处理页码变化
 */
const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchNotifications()
}

/**
 * 处理每页数量变化
 */
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  fetchNotifications()
}

/**
 * 标记单条消息为已读
 */
const handleMarkRead = async (notificationId: number) => {
  try {
    await notificationApi.markAsRead(notificationId)
    
    // 更新本地状态
    const notification = notifications.value.find(n => n.id === notificationId)
    if (notification) {
      notification.is_read = true
      notification.read_at = new Date().toISOString()
    }
    
    ElMessage.success('已标记为已读')
    emit('notificationRead')
  } catch (error) {
    console.error('Failed to mark as read:', error)
    ElMessage.error('标记已读失败')
  }
}

/**
 * 一键标记全部已读
 */
const handleMarkAllRead = async () => {
  markingAllRead.value = true
  try {
    await notificationApi.markAllAsRead()
    
    // 更新本地状态
    notifications.value.forEach(notification => {
      notification.is_read = true
      notification.read_at = new Date().toISOString()
    })
    
    ElMessage.success('已全部标记为已读')
    emit('allRead')
  } catch (error) {
    console.error('Failed to mark all as read:', error)
    ElMessage.error('标记全部已读失败')
  } finally {
    markingAllRead.value = false
  }
}

/**
 * 处理通知点击
 * 如果有链接，跳转到对应页面
 */
const handleNotificationClick = async (notification: Notification) => {
  // 如果未读，先标记为已读
  if (!notification.is_read) {
    await handleMarkRead(notification.id)
  }
  
  // 如果有链接，跳转
  if (notification.link) {
    router.push(notification.link)
  }
}

/**
 * 格式化时间
 * 显示相对时间（如：刚刚、5分钟前、1小时前、昨天、2天前）
 */
const formatTime = (dateString: string): string => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (seconds < 60) {
    return '刚刚'
  } else if (minutes < 60) {
    return `${minutes}分钟前`
  } else if (hours < 24) {
    return `${hours}小时前`
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days}天前`
  } else {
    // 超过7天显示具体日期
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }
}

/**
 * 组件挂载时加载数据
 */
onMounted(() => {
  fetchNotifications()
})
</script>

<style scoped lang="scss">
.notification-list {
  display: flex;
  flex-direction: column;
  height: 100%;
  
  .notification-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    border-bottom: 1px solid #ebeef5;
    
    .type-filter {
      flex: 1;
      max-width: 200px;
      margin-right: 12px;
    }
  }
  
  .notification-content {
    flex: 1;
    overflow-y: auto;
    
    .notification-items {
      .notification-item {
        position: relative;
        display: flex;
        padding: 16px;
        border-bottom: 1px solid #ebeef5;
        cursor: pointer;
        transition: background-color 0.3s ease;
        
        &:hover {
          background-color: #f5f7fa;
        }
        
        &.is-read {
          opacity: 0.6;
          
          .notification-title {
            font-weight: normal;
          }
        }
        
        .unread-dot {
          position: absolute;
          top: 20px;
          left: 8px;
          width: 8px;
          height: 8px;
          background-color: #f56c6c;
          border-radius: 50%;
        }
        
        .notification-body {
          flex: 1;
          padding-left: 8px;
          
          .type-tag {
            margin-bottom: 8px;
          }
          
          .notification-title {
            font-size: 14px;
            font-weight: 600;
            color: #303133;
            margin-bottom: 8px;
            line-height: 1.4;
          }
          
          .notification-text {
            font-size: 13px;
            color: #606266;
            margin-bottom: 8px;
            line-height: 1.5;
            word-break: break-word;
          }
          
          .notification-time {
            font-size: 12px;
            color: #909399;
          }
        }
        
        .notification-actions {
          display: flex;
          align-items: flex-start;
          padding-top: 4px;
        }
      }
    }
    
    .notification-pagination {
      padding: 16px;
      display: flex;
      justify-content: center;
      border-top: 1px solid #ebeef5;
    }
  }
}

/**
 * 移动端适配
 */
@media (max-width: 768px) {
  .notification-list {
    .notification-header {
      flex-direction: column;
      align-items: stretch;
      
      .type-filter {
        max-width: 100%;
        margin-right: 0;
        margin-bottom: 12px;
      }
    }
    
    .notification-content {
      .notification-items {
        .notification-item {
          flex-direction: column;
          
          .notification-actions {
            margin-top: 12px;
            justify-content: flex-end;
          }
        }
      }
    }
  }
}
</style>
