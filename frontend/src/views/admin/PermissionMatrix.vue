<template>
  <div class="permission-matrix-container p-4 md:p-6">
    <el-card>
      <template #header>
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-xl font-bold">权限矩阵</h2>
            <p class="mt-1 text-sm text-gray-500">按用户维护模块 + 操作权限，变更会按用户批量提交。</p>
          </div>
          <div class="flex gap-2">
            <el-button type="primary" :loading="saving" @click="saveAllChanges">
              保存变更
            </el-button>
            <el-button :icon="Refresh" circle @click="loadPermissionMatrix" />
          </div>
        </div>
      </template>

      <div v-if="loading" class="py-10 text-center">
        <el-icon class="is-loading text-4xl"><Loading /></el-icon>
        <p class="mt-3 text-gray-500">正在加载权限矩阵...</p>
      </div>

      <div v-else class="permission-matrix-table overflow-x-auto">
        <table class="w-full border-collapse">
          <thead>
            <tr class="bg-gray-100">
              <th class="sticky-col min-w-[220px] border p-3 text-left">用户</th>
              <th
                v-for="module in modules"
                :key="module.module_path"
                :colspan="module.operations.length"
                class="border p-3 text-center"
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
                  class="min-w-[84px] border p-2 text-center text-sm"
                >
                  {{ operationLabels[operation] }}
                </th>
              </template>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in permissionRows" :key="row.user.id" class="hover:bg-gray-50">
              <td class="sticky-col border bg-white p-3">
                <div class="flex flex-col gap-1">
                  <div class="flex items-center gap-2">
                    <span class="font-medium">{{ row.user.full_name }}</span>
                    <el-tag v-if="row.user.is_platform_admin" type="danger" size="small">平台管理员</el-tag>
                  </div>
                  <span class="text-xs text-gray-500">{{ row.user.username }}</span>
                  <div class="flex gap-2">
                    <el-tag size="small" :type="row.user.user_type === 'internal' ? 'primary' : 'success'">
                      {{ row.user.user_type === 'internal' ? '内部员工' : '供应商' }}
                    </el-tag>
                    <el-tag v-if="row.user.supplier_name" size="small" type="info">
                      {{ row.user.supplier_name }}
                    </el-tag>
                  </div>
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

        <div v-if="permissionRows.length === 0" class="py-10 text-center text-gray-500">
          当前没有可展示的用户权限数据。
        </div>
      </div>

      <el-alert v-if="hasChanges" type="warning" :closable="false" class="mt-4">
        <template #title>还有 {{ changedCount }} 项权限变更未保存。</template>
      </el-alert>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, Refresh } from '@element-plus/icons-vue'
import { adminApi } from '@/api/admin'
import type { OperationType, PermissionMatrixColumn, PermissionMatrixRow } from '@/types/admin'

const operationLabels: Record<OperationType, string> = {
  create: '录入',
  read: '查看',
  update: '修改',
  delete: '删除',
  export: '导出'
}

const loading = ref(false)
const saving = ref(false)
const modules = ref<PermissionMatrixColumn[]>([])
const permissionRows = ref<PermissionMatrixRow[]>([])

interface PermissionChange {
  user_id: number
  module_path: string
  operation_type: OperationType
  is_granted: boolean
}

const pendingChanges = ref<PermissionChange[]>([])
const hasChanges = computed(() => pendingChanges.value.length > 0)
const changedCount = computed(() => pendingChanges.value.length)

async function loadPermissionMatrix() {
  loading.value = true
  try {
    const response = await adminApi.getPermissionMatrix()
    modules.value = response.modules
    permissionRows.value = response.rows
    pendingChanges.value = []
  } catch (error: any) {
    ElMessage.error(error.message || '加载权限矩阵失败')
  } finally {
    loading.value = false
  }
}

function handlePermissionChange(
  userId: number,
  modulePath: string,
  operation: OperationType,
  isGranted: boolean | string | number
) {
  const granted = Boolean(isGranted)
  const changeKey = `${userId}-${modulePath}-${operation}`

  pendingChanges.value = pendingChanges.value.filter(
    (change) => `${change.user_id}-${change.module_path}-${change.operation_type}` !== changeKey
  )

  pendingChanges.value.push({
    user_id: userId,
    module_path: modulePath,
    operation_type: operation,
    is_granted: granted
  })
}

function groupByUser(changes: PermissionChange[]) {
  return changes.reduce<Record<number, PermissionChange[]>>((acc, change) => {
    if (!acc[change.user_id]) {
      acc[change.user_id] = []
    }
    acc[change.user_id].push(change)
    return acc
  }, {})
}

async function saveAllChanges() {
  if (!hasChanges.value) {
    ElMessage.info('没有需要保存的变更')
    return
  }

  saving.value = true
  try {
    const toGrant = pendingChanges.value.filter((change) => change.is_granted)
    const toRevoke = pendingChanges.value.filter((change) => !change.is_granted)

    for (const [userId, permissions] of Object.entries(groupByUser(toGrant))) {
      await adminApi.grantPermissions({
        user_ids: [Number(userId)],
        permissions: permissions.map((item) => ({
          module_path: item.module_path,
          operation_type: item.operation_type
        }))
      })
    }

    for (const [userId, permissions] of Object.entries(groupByUser(toRevoke))) {
      await adminApi.revokePermissions({
        user_ids: [Number(userId)],
        permissions: permissions.map((item) => ({
          module_path: item.module_path,
          operation_type: item.operation_type
        }))
      })
    }

    ElMessage.success(`已保存 ${changedCount.value} 项权限变更`)
    await loadPermissionMatrix()
  } catch (error: any) {
    ElMessage.error(error.message || '保存权限变更失败')
  } finally {
    saving.value = false
  }
}

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
  max-height: calc(100vh - 280px);
}

.sticky-col {
  position: sticky;
  left: 0;
  z-index: 10;
}

table,
th,
td {
  border: 1px solid #dcdfe6;
}

thead tr {
  position: sticky;
  top: 0;
  z-index: 20;
}

thead tr:nth-child(2) {
  top: 49px;
}
</style>
