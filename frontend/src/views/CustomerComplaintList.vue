<template>
  <div class="customer-complaint-list p-4 md:p-6">
    <div class="mb-6 flex flex-col md:flex-row md:items-center md:justify-between">
      <h1 class="mb-4 text-2xl font-bold md:mb-0">客诉管理</h1>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon class="mr-1"><Plus /></el-icon>
        创建客诉单
      </el-button>
    </div>

    <el-card class="mb-4">
      <el-form :model="queryParams" inline class="flex flex-wrap gap-2">
        <el-form-item label="客诉类型">
          <el-select v-model="queryParams.complaint_type" placeholder="全部" clearable class="w-full md:w-40">
            <el-option
              v-for="option in complaintTypeOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="客户">
          <el-select
            v-model="queryParams.customer_id"
            filterable
            clearable
            placeholder="全部"
            class="w-full md:w-56"
          >
            <el-option
              v-for="item in customerOptions"
              :key="item.id"
              :label="`${item.name} (${item.code})`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="产品类型">
          <el-input
            v-model="queryParams.product_type"
            placeholder="请输入"
            clearable
            class="w-full md:w-40"
          />
        </el-form-item>

        <el-form-item label="状态">
          <el-select v-model="queryParams.status" placeholder="全部" clearable class="w-full md:w-40">
            <el-option
              v-for="option in statusOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="日期范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            class="w-full md:w-64"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <el-table v-loading="loading" :data="complaintList" stripe class="w-full">
        <el-table-column prop="complaint_number" label="客诉编号" width="160" fixed />
        <el-table-column prop="complaint_type" label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.complaint_type === ComplaintType.ZERO_KM ? 'danger' : 'warning'">
              {{ getComplaintTypeLabel(row.complaint_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="客户" min-width="220">
          <template #default="{ row }">
            <div class="font-medium">{{ row.customer_name || row.customer_code }}</div>
            <div class="text-xs text-gray-500">{{ row.customer_code }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="end_customer_name" label="终端客户" min-width="160">
          <template #default="{ row }">{{ row.end_customer_name || '-' }}</template>
        </el-table-column>
        <el-table-column prop="product_type" label="产品类型" width="140" />
        <el-table-column prop="defect_description" label="缺陷描述" min-width="220" show-overflow-tooltip />
        <el-table-column label="退件" width="90">
          <template #default="{ row }">
            <el-tag :type="row.is_return_required ? 'warning' : 'info'">
              {{ row.is_return_required ? '涉及' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="实物解析" width="110">
          <template #default="{ row }">
            <el-tag :type="row.requires_physical_analysis ? 'primary' : 'success'">
              {{ row.requires_physical_analysis ? '需解析' : '免解析' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="severity_level" label="严重度" width="100" />
        <el-table-column prop="status" label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="getCustomerComplaintStatusType(row.status)">
              {{ getCustomerComplaintStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleView(row)">查看</el-button>
            <el-button
              v-if="canSubmitCustomerComplaintAnalysis(row)"
              link
              type="primary"
              size="small"
              @click="handleAnalysis(row)"
            >
              一次因解析
            </el-button>
            <el-button
              v-if="canOpenCustomerComplaintEightD(row)"
              link
              type="primary"
              size="small"
              @click="handle8D(row)"
            >
              8D报告
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="mt-4 flex justify-end">
        <el-pagination
          v-model:current-page="queryParams.page"
          v-model:page-size="queryParams.page_size"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadComplaints"
          @current-change="loadComplaints"
        />
      </div>
    </el-card>

    <el-dialog
      v-model="showCreateDialog"
      title="创建客诉单"
      width="90%"
      :close-on-click-modal="false"
      class="max-w-2xl"
    >
      <CustomerComplaintForm @success="handleCreateSuccess" @cancel="showCreateDialog = false" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getCustomerComplaintCustomerOptions,
  getCustomerComplaints,
} from '@/api/customer-quality'
import CustomerComplaintForm from '@/components/CustomerComplaintForm.vue'
import { useProblemManagementStore } from '@/stores/problemManagement'
import type {
  CustomerComplaint,
  CustomerComplaintCustomerOption,
  CustomerComplaintListQuery,
} from '@/types/customer-quality'
import { ComplaintType } from '@/types/customer-quality'
import {
  buildCustomerComplaintTypeOptions,
  getCustomerComplaintTypeLabel as resolveCustomerComplaintTypeLabel,
} from '@/utils/problemManagement'
import {
  buildCustomerComplaintStatusOptions,
  canOpenCustomerComplaintEightD,
  canSubmitCustomerComplaintAnalysis,
  getCustomerComplaintStatusLabel,
  getCustomerComplaintStatusType,
} from '@/utils/customerComplaint'

const router = useRouter()
const problemManagementStore = useProblemManagementStore()

const loading = ref(false)
const complaintList = ref<CustomerComplaint[]>([])
const customerOptions = ref<CustomerComplaintCustomerOption[]>([])
const total = ref(0)
const showCreateDialog = ref(false)
const dateRange = ref<[string, string] | null>(null)

const queryParams = reactive<CustomerComplaintListQuery>({
  page: 1,
  page_size: 20,
  complaint_type: undefined,
  customer_id: undefined,
  product_type: undefined,
  status: undefined,
  start_date: undefined,
  end_date: undefined,
})

const complaintTypeOptions = computed(() =>
  buildCustomerComplaintTypeOptions(problemManagementStore.getCategory)
)

const statusOptions = buildCustomerComplaintStatusOptions()

function getComplaintTypeLabel(complaintType: ComplaintType): string {
  return resolveCustomerComplaintTypeLabel(complaintType, problemManagementStore.getCategory)
}

async function loadCustomerOptions() {
  try {
    customerOptions.value = await getCustomerComplaintCustomerOptions()
  } catch (error: any) {
    ElMessage.error(error.message || '加载客户清单失败')
  }
}

async function loadComplaints() {
  loading.value = true

  try {
    if (dateRange.value) {
      queryParams.start_date = dateRange.value[0]
      queryParams.end_date = dateRange.value[1]
    } else {
      queryParams.start_date = undefined
      queryParams.end_date = undefined
    }

    const response = await getCustomerComplaints(queryParams)
    complaintList.value = response.items
    total.value = response.total
  } catch (error: any) {
    ElMessage.error(error.message || '加载客诉单列表失败')
    console.error('Load complaints error:', error)
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  queryParams.page = 1
  void loadComplaints()
}

function handleReset() {
  queryParams.page = 1
  queryParams.page_size = 20
  queryParams.complaint_type = undefined
  queryParams.customer_id = undefined
  queryParams.product_type = undefined
  queryParams.status = undefined
  dateRange.value = null
  void loadComplaints()
}

function handleView(row: CustomerComplaint) {
  router.push(`/customer-complaints/${row.id}`)
}

function handleAnalysis(row: CustomerComplaint) {
  router.push(`/customer-complaints/${row.id}/analysis`)
}

function handle8D(row: CustomerComplaint) {
  router.push(`/customer-complaints/${row.id}/8d`)
}

function handleCreateSuccess() {
  showCreateDialog.value = false
  ElMessage.success('客诉单创建成功')
  void loadComplaints()
}

onMounted(() => {
  void problemManagementStore.loadCatalog()
  void loadCustomerOptions()
  void loadComplaints()
})
</script>

<style scoped>
.customer-complaint-list {
  min-height: 100vh;
}

@media (max-width: 768px) {
  :deep(.el-table) {
    font-size: 12px;
  }

  :deep(.el-button) {
    padding: 4px 8px;
    font-size: 12px;
  }
}
</style>
