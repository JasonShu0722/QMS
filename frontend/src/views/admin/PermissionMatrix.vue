<template>
  <div class="permission-matrix-container p-4 md:p-6">
    <el-card>
      <template #header>
        <div class="flex justify-between items-center">
          <h2 class="text-xl font-bold">权限矩阵配置</h2>
          <div class="flex gap-2">
            <el-button @click="saveAllChanges" type="primary" :loading="saving">
              保存所有更改
            </el-button>
            <el-button @click="loadPermissionMatrix" :icon="Refresh" circle />
          </div>
        </div>
      </template>

      <!-- 加载状态 -->
      <div v-if="loading" class="text-center py-8">
        <el-icon class="is-loading text-4xl">
          <Loading />
        </el-icon>
        <p class="mt-2 text-gray-500">加载中...</p>
      </div>

      <!-- 权限矩阵表格 -->
      <div v-else class="permission-matrix-table overflow-x-auto">
        <table class="w-full border-collapse">
          <thead>
            <tr class="bg-gray-100">
              <th class="sticky-col border p-2 text-left min-w-[150px]">
                用户
              </th>
              <th
                v-for="module in modules"
                :key="module.module_path"
                :colspan="module.operations.length"
                class="border p-2 text-center"
              >
                {{ module.module_name }}
              </th>
            </tr>
            <tr class="bg-gray-50">
              <th class="sticky-col border p-2"></th>
              <template v-for="module in modules" :key="module.module_path">
                <th
                  v-for="operation in module.operations"
                  :key="`${module.module_path}.${operation}`"
                  class="border p-2 text-center text-sm min-w-[80px]"
                >
                  {{ operationLabels[operation] }}
                </th>
              </template>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in permissionMatrix"
              :key="row.user.id"
              class="hover:bg-gray-50"
            >
              <td class="sticky-col border p-2 bg-white">
                <div class="flex flex-col">
                  <span class="font-medium">{{ row.user.full_name }}</span>
                  <span class="text-xs text-gray-500">{{ row.user.username }}</span>
                  <el-tag
                    size="small"
                    :type="row.user.user_type === 'internal' ? 'primary' : 'success'"
                    class="mt-1"
                  >
                    {{ row.user.user_type === 'internal' ? '内部' : '供应商' }}
                  </el-tag>
                </div>
              </td>
              <template v-for="module in modules" :key="module.module_path">
                <td
                  v-for="operation in module.operations"
                  :key="`${module.module_path}.${operation}`"
                  class="border p-2 text-center"
                >
                  <el-checkbox
                    v-model="row.permissions[`${module.module_path}.${operation}`]"
                    @change="handlePermissionChange(row.user.id, module.module_path, operation, $event)"
                  />
                </td>
              </template>
            </tr>
          </tbody>
        </table>

        <!-- 空状态 -->
        <div v-if="permissionMatrix.length === 0" class="text-center py-8 text-gray-500">
          暂无用户数据
        </div>
      </div>

      <!-- 变更提示 -->
      <el-alert
        v-if="hasChanges"
        type="warning"
        :closable="false"
        class="mt-4"
      >
        <template #title>
          您有 {{ changedCount }} 项权限变更尚未保存，请点击"保存所有更改"按钮
        </template>
      </el-alert>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Loading } from '@element-plus/icons-vue'
import { adminApi } from '@/api/admin'
import type { PermissionMatrixRow, PermissionMatrixColumn, OperationType } from '@/types/admin'

// 操作类型标签映射
const operationLabels: Record<OperationType, string> = {
  create: '录入',
  read: '查阅',
  update: '修改',
  delete: '删除',
  export: '导出'
}

// 状态
const loading = ref(false)
const saving = ref(false)
const modules = ref<PermissionMatrixColumn[]>([])
const permissionMatrix = ref<PermissionMatrixRow[]>([])

// 变更追踪
interface PermissionChange {
  user_id: number
  module_path: string
  operation_type: OperationType
  is_granted: boolean
}
const pendingChanges = ref<PermissionChange[]>([])

// 计算属性
const hasChanges = computed(() => pendingChanges.value.length > 0)
const changedCount = computed(() => pendingChanges.value.length)

/**
 * 加载权限矩阵
 */
async function loadPermissionMatrix() {
  loading.value = true
  try {
    const response = await adminApi.getPermissionMatrix()
    modules.value = response.modules
    permissionMatrix.value = response.permissions
    pendingChanges.value = []
  } catch (error: any) {
    ElMessage.error(error.message || '加载权限矩阵失败')
  } finally {
    loading.value = false
  }
}

/**
 * 处理权限变更
 */
function handlePermissionChange(
  userId: number,
  modulePath: string,
  operation: OperationType,
  isGranted: boolean | string | number
) {
  const granted = Boolean(isGranted)
  const changeKey = `${userId}-${modulePath}-${operation}`
  
  // 移除旧的变更记录
  pendingChanges.value = pendingChanges.value.filter(
    change => `${change.user_id}-${change.module_path}-${change.operation_type}` !== changeKey
  )
  
  // 添加新的变更记录
  pendingChanges.value.push({
    user_id: userId,
    module_path: modulePath,
    operation_type: operation,
    is_granted: granted
  })
}

/**
 * 保存所有变更
 */
async function saveAllChanges() {
  if (!hasChanges.value) {
    ElMessage.info('没有需要保存的变更')
    return
  }

  saving.value = true
  try {
    // 分组：授予权限和撤销权限
    const toGrant = pendingChanges.value.filter(c => c.is_granted)
    const toRevoke = pendingChanges.value.filter(c => !c.is_granted)

    // 批量授予权限
    if (toGrant.length > 0) {
      const grantByUser = groupByUser(toGrant)
      for (const [userId, permissions] of Object.entries(grantByUser)) {
        await adminApi.grantPermissions({
          user_ids: [Number(userId)],
          permissions: permissions.map(p => ({
            module_path: p.module_path,
            operation_type: p.operation_type
          }))
        })
      }
    }

    // 批量撤销权限
    if (toRevoke.length > 0) {
      const revokeByUser = groupByUser(toRevoke)
      for (const [userId, permissions] of Object.entries(revokeByUser)) {
        await adminApi.revokePermissions({
          user_ids: [Number(userId)],
          permissions: permissions.map(p => ({
            module_path: p.module_path,
            operation_type: p.operation_type
          }))
        })
      }
    }

    ElMessage.success(`成功保存 ${changedCount.value} 项权限变更`)
    pendingChanges.value = []
  } catch (error: any) {
    ElMessage.error(error.message || '保存权限变更失败')
  } finally {
    saving.value = false
  }
}

/**
 * 按用户分组变更
 */
function groupByUser(changes: PermissionChange[]): Record<number, PermissionChange[]> {
  return changes.reduce((acc, change) => {
    if (!acc[change.user_id]) {
      acc[change.user_id] = []
    }
    acc[change.user_id].push(change)
    return acc
  }, {} as Record<number, PermissionChange[]>)
}

// 初始化
onMounted(() => {
  loadPermissionMatrix()
})
</script>

<style scoped>
.permission-matrix-container {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.permission-matrix-table {
  max-height: calc(100vh - 300px);
}

.sticky-col {
  position: sticky;
  left: 0;
  z-index: 10;
  background-color: white;
}

table {
  border: 1px solid #dcdfe6;
}

th,
td {
  border: 1px solid #dcdfe6;
}

thead tr {
  position: sticky;
  top: 0;
  z-index: 20;
}

thead tr:first-child {
  top: 0;
}

thead tr:nth-child(2) {
  top: 41px;
}
</style>
