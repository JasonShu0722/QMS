<template>
  <div class="user-approval-container p-4 md:p-6">
    <el-card>
      <template #header>
        <div class="flex justify-between items-center">
          <h2 class="text-xl font-bold">用户审核管理</h2>
          <el-button @click="loadPendingUsers" :icon="Refresh" circle />
        </div>
      </template>

      <!-- 加载状态 -->
      <div v-if="loading" class="text-center py-8">
        <el-icon class="is-loading text-4xl">
          <Loading />
        </el-icon>
        <p class="mt-2 text-gray-500">加载中...</p>
      </div>

      <!-- 待审核用户列表 -->
      <el-table
        v-else
        :data="pendingUsers"
        stripe
        class="w-full"
        :empty-text="'暂无待审核用户'"
      >
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="full_name" label="姓名" width="100" />
        <el-table-column prop="user_type" label="用户类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.user_type === 'internal' ? 'primary' : 'success'">
              {{ row.user_type === 'internal' ? '内部员工' : '供应商' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="180" />
        <el-table-column prop="phone" label="电话" width="120" />
        <el-table-column label="部门/供应商" min-width="150">
          <template #default="{ row }">
            {{ row.user_type === 'internal' ? row.department : row.supplier_name }}
          </template>
        </el-table-column>
        <el-table-column prop="position" label="职位" width="120" />
        <el-table-column prop="created_at" label="申请时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              type="success"
              size="small"
              @click="handleApprove(row)"
              :loading="actionLoading[row.id]"
            >
              批准
            </el-button>
            <el-button
              type="danger"
              size="small"
              @click="handleReject(row)"
              :loading="actionLoading[row.id]"
            >
              拒绝
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 拒绝原因对话框 -->
    <el-dialog
      v-model="rejectDialogVisible"
      title="拒绝用户注册"
      width="500px"
    >
      <el-form :model="rejectForm" label-width="100px">
        <el-form-item label="用户名">
          <span>{{ currentUser?.username }}</span>
        </el-form-item>
        <el-form-item label="姓名">
          <span>{{ currentUser?.full_name }}</span>
        </el-form-item>
        <el-form-item label="拒绝原因" required>
          <el-input
            v-model="rejectForm.reason"
            type="textarea"
            :rows="4"
            placeholder="请输入拒绝原因（必填）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="rejectDialogVisible = false">取消</el-button>
        <el-button
          type="danger"
          @click="confirmReject"
          :loading="actionLoading[currentUser?.id || 0]"
          :disabled="!rejectForm.reason.trim()"
        >
          确认拒绝
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Loading } from '@element-plus/icons-vue'
import { adminApi } from '@/api/admin'
import type { User } from '@/types/user'

// 状态
const loading = ref(false)
const pendingUsers = ref<User[]>([])
const actionLoading = reactive<Record<number, boolean>>({})
const rejectDialogVisible = ref(false)
const currentUser = ref<User | null>(null)
const rejectForm = reactive({
  reason: ''
})

/**
 * 加载待审核用户列表
 */
async function loadPendingUsers() {
  loading.value = true
  try {
    pendingUsers.value = await adminApi.getPendingUsers()
  } catch (error: any) {
    ElMessage.error(error.message || '加载待审核用户失败')
  } finally {
    loading.value = false
  }
}

/**
 * 批准用户
 */
async function handleApprove(user: User) {
  try {
    await ElMessageBox.confirm(
      `确认批准用户 "${user.full_name} (${user.username})" 的注册申请？`,
      '确认批准',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'success'
      }
    )

    actionLoading[user.id] = true
    await adminApi.approveUser(user.id)
    ElMessage.success('用户已批准，激活通知邮件已发送')
    
    // 从列表中移除
    pendingUsers.value = pendingUsers.value.filter(u => u.id !== user.id)
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '批准用户失败')
    }
  } finally {
    actionLoading[user.id] = false
  }
}

/**
 * 拒绝用户
 */
function handleReject(user: User) {
  currentUser.value = user
  rejectForm.reason = ''
  rejectDialogVisible.value = true
}

/**
 * 确认拒绝
 */
async function confirmReject() {
  if (!currentUser.value || !rejectForm.reason.trim()) {
    return
  }

  const userId = currentUser.value.id
  actionLoading[userId] = true

  try {
    await adminApi.rejectUser(userId, rejectForm.reason)
    ElMessage.success('用户已拒绝')
    
    // 从列表中移除
    pendingUsers.value = pendingUsers.value.filter(u => u.id !== userId)
    rejectDialogVisible.value = false
  } catch (error: any) {
    ElMessage.error(error.message || '拒绝用户失败')
  } finally {
    actionLoading[userId] = false
  }
}

/**
 * 格式化日期
 */
function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 初始化
onMounted(() => {
  loadPendingUsers()
})
</script>

<style scoped>
.user-approval-container {
  min-height: 100vh;
  background-color: #f5f7fa;
}
</style>
