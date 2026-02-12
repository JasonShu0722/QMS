<template>
  <div class="feature-flags-container p-4 md:p-6">
    <el-card>
      <template #header>
        <div class="flex justify-between items-center">
          <h2 class="text-xl font-bold">功能开关管理</h2>
          <el-button @click="loadFeatureFlags" :icon="Refresh" circle />
        </div>
      </template>

      <!-- 功能开关列表 -->
      <div v-loading="loading">
        <el-table :data="featureFlags" stripe class="w-full">
          <el-table-column prop="feature_name" label="功能名称" min-width="180">
            <template #default="{ row }">
              <div>
                <div class="font-medium">{{ row.feature_name }}</div>
                <div class="text-xs text-gray-500">{{ row.feature_key }}</div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="description" label="功能描述" min-width="250" show-overflow-tooltip />
          
          <el-table-column label="状态" width="100" align="center">
            <template #default="{ row }">
              <el-switch
                v-model="row.is_enabled"
                @change="handleToggle(row)"
                :loading="toggleLoading[row.id]"
              />
            </template>
          </el-table-column>
          
          <el-table-column label="作用范围" width="120">
            <template #default="{ row }">
              <el-tag :type="row.scope === 'global' ? 'success' : 'warning'">
                {{ row.scope === 'global' ? '全局' : '白名单' }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column label="白名单" width="150">
            <template #default="{ row }">
              <div v-if="row.scope === 'whitelist'" class="text-sm">
                <div v-if="row.whitelist_user_ids?.length">
                  用户: {{ row.whitelist_user_ids.length }} 个
                </div>
                <div v-if="row.whitelist_supplier_ids?.length">
                  供应商: {{ row.whitelist_supplier_ids.length }} 个
                </div>
                <div v-if="!row.whitelist_user_ids?.length && !row.whitelist_supplier_ids?.length" class="text-gray-400">
                  未配置
                </div>
              </div>
              <span v-else class="text-gray-400">-</span>
            </template>
          </el-table-column>
          
          <el-table-column label="环境" width="100">
            <template #default="{ row }">
              <el-tag :type="row.environment === 'stable' ? 'primary' : 'info'" size="small">
                {{ row.environment === 'stable' ? '正式' : '预览' }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="updated_at" label="更新时间" width="160">
            <template #default="{ row }">
              {{ formatDate(row.updated_at) }}
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button
                type="primary"
                size="small"
                @click="showConfigDialog(row)"
              >
                配置
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 空状态 -->
        <div v-if="featureFlags.length === 0 && !loading" class="text-center py-8 text-gray-500">
          暂无功能开关数据
        </div>
      </div>
    </el-card>

    <!-- 配置对话框 -->
    <el-dialog
      v-model="configDialogVisible"
      :title="`配置功能开关: ${currentFlag?.feature_name}`"
      width="600px"
      destroy-on-close
    >
      <el-form
        v-if="currentFlag"
        :model="configForm"
        label-width="120px"
      >
        <el-form-item label="功能名称">
          <span>{{ currentFlag.feature_name }}</span>
        </el-form-item>
        
        <el-form-item label="功能标识">
          <span class="text-gray-500">{{ currentFlag.feature_key }}</span>
        </el-form-item>
        
        <el-form-item label="功能描述">
          <span>{{ currentFlag.description }}</span>
        </el-form-item>
        
        <el-form-item label="启用状态">
          <el-switch v-model="configForm.is_enabled" />
          <span class="ml-2 text-sm text-gray-500">
            {{ configForm.is_enabled ? '已启用' : '已禁用' }}
          </span>
        </el-form-item>
        
        <el-form-item label="作用范围">
          <el-radio-group v-model="configForm.scope">
            <el-radio label="global">全局生效</el-radio>
            <el-radio label="whitelist">白名单机制</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <!-- 白名单配置 -->
        <template v-if="configForm.scope === 'whitelist'">
          <el-form-item label="用户白名单">
            <el-select
              v-model="configForm.whitelist_user_ids"
              multiple
              filterable
              placeholder="请选择用户"
              style="width: 100%"
            >
              <el-option
                v-for="user in availableUsers"
                :key="user.id"
                :label="`${user.full_name} (${user.username})`"
                :value="user.id"
              />
            </el-select>
            <div class="text-xs text-gray-500 mt-1">
              已选择 {{ configForm.whitelist_user_ids?.length || 0 }} 个用户
            </div>
          </el-form-item>
          
          <el-form-item label="供应商白名单">
            <el-select
              v-model="configForm.whitelist_supplier_ids"
              multiple
              filterable
              placeholder="请选择供应商"
              style="width: 100%"
            >
              <el-option
                v-for="supplier in availableSuppliers"
                :key="supplier.id"
                :label="`${supplier.name} (${supplier.code})`"
                :value="supplier.id"
              />
            </el-select>
            <div class="text-xs text-gray-500 mt-1">
              已选择 {{ configForm.whitelist_supplier_ids?.length || 0 }} 个供应商
            </div>
          </el-form-item>
        </template>
        
        <el-alert
          v-if="configForm.scope === 'global'"
          type="info"
          :closable="false"
          class="mb-4"
        >
          全局模式下，功能将对所有用户生效（如果启用）
        </el-alert>
        
        <el-alert
          v-if="configForm.scope === 'whitelist' && configForm.is_enabled"
          type="warning"
          :closable="false"
          class="mb-4"
        >
          白名单模式下，仅指定的用户或供应商可以使用此功能
        </el-alert>
      </el-form>
      
      <template #footer>
        <el-button @click="configDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          @click="saveConfig"
          :loading="saving"
        >
          保存配置
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { adminApi } from '@/api/admin'
import type { FeatureFlag, FeatureFlagUpdateRequest } from '@/types/admin'
import type { User } from '@/types/user'

// 供应商类型定义
interface Supplier {
  id: number
  name: string
  code: string
}

// 状态
const loading = ref(false)
const saving = ref(false)
const featureFlags = ref<FeatureFlag[]>([])
const toggleLoading = reactive<Record<number, boolean>>({})

// 配置对话框
const configDialogVisible = ref(false)
const currentFlag = ref<FeatureFlag | null>(null)
const configForm = reactive<FeatureFlagUpdateRequest>({
  is_enabled: false,
  scope: 'global',
  whitelist_user_ids: [],
  whitelist_supplier_ids: []
})

// 白名单选项
const availableUsers = ref<User[]>([])
const availableSuppliers = ref<Supplier[]>([])

/**
 * 加载功能开关列表
 */
async function loadFeatureFlags() {
  loading.value = true
  try {
    featureFlags.value = await adminApi.getFeatureFlags()
  } catch (error: any) {
    ElMessage.error(error.message || '加载功能开关失败')
  } finally {
    loading.value = false
  }
}

/**
 * 处理开关切换
 */
async function handleToggle(flag: FeatureFlag) {
  try {
    await ElMessageBox.confirm(
      `确认${flag.is_enabled ? '启用' : '禁用'}功能 "${flag.feature_name}"？`,
      '确认操作',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: flag.is_enabled ? 'success' : 'warning'
      }
    )

    toggleLoading[flag.id] = true
    await adminApi.updateFeatureFlag(flag.id, {
      is_enabled: flag.is_enabled,
      scope: flag.scope,
      whitelist_user_ids: flag.whitelist_user_ids,
      whitelist_supplier_ids: flag.whitelist_supplier_ids
    })
    
    ElMessage.success(`功能已${flag.is_enabled ? '启用' : '禁用'}`)
  } catch (error: any) {
    if (error !== 'cancel') {
      // 恢复开关状态
      flag.is_enabled = !flag.is_enabled
      ElMessage.error(error.message || '操作失败')
    } else {
      // 用户取消，恢复开关状态
      flag.is_enabled = !flag.is_enabled
    }
  } finally {
    toggleLoading[flag.id] = false
  }
}

/**
 * 显示配置对话框
 */
async function showConfigDialog(flag: FeatureFlag) {
  try {
    // 加载完整的功能开关详情
    currentFlag.value = await adminApi.getFeatureFlagDetail(flag.id)
    
    // 初始化表单
    configForm.is_enabled = currentFlag.value.is_enabled
    configForm.scope = currentFlag.value.scope
    configForm.whitelist_user_ids = currentFlag.value.whitelist_user_ids || []
    configForm.whitelist_supplier_ids = currentFlag.value.whitelist_supplier_ids || []
    
    configDialogVisible.value = true
    
    // TODO: 加载可用用户和供应商列表
  } catch (error: any) {
    ElMessage.error(error.message || '加载功能开关详情失败')
  }
}

/**
 * 保存配置
 */
async function saveConfig() {
  if (!currentFlag.value) {
    return
  }

  // 验证白名单配置
  if (configForm.scope === 'whitelist' && configForm.is_enabled) {
    if (
      (!configForm.whitelist_user_ids || configForm.whitelist_user_ids.length === 0) &&
      (!configForm.whitelist_supplier_ids || configForm.whitelist_supplier_ids.length === 0)
    ) {
      ElMessage.warning('白名单模式下至少需要配置一个用户或供应商')
      return
    }
  }

  saving.value = true
  try {
    await adminApi.updateFeatureFlag(currentFlag.value.id, {
      is_enabled: configForm.is_enabled,
      scope: configForm.scope,
      whitelist_user_ids: configForm.scope === 'whitelist' ? configForm.whitelist_user_ids : [],
      whitelist_supplier_ids: configForm.scope === 'whitelist' ? configForm.whitelist_supplier_ids : []
    })
    
    ElMessage.success('配置保存成功')
    configDialogVisible.value = false
    
    // 刷新列表
    await loadFeatureFlags()
  } catch (error: any) {
    ElMessage.error(error.message || '保存配置失败')
  } finally {
    saving.value = false
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
  loadFeatureFlags()
  // TODO: 加载可用用户和供应商列表
})
</script>

<style scoped>
.feature-flags-container {
  min-height: 100vh;
  background-color: #f5f7fa;
}
</style>
