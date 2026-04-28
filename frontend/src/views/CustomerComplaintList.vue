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
          <el-input v-model="queryParams.product_type" placeholder="请输入" clearable class="w-full md:w-40" />
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
      <div class="mb-4 flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div class="text-sm text-gray-500">
          {{ batchLaunchSummary }}
        </div>
        <el-button
          type="primary"
          plain
          :disabled="!canBatchLaunchEightD"
          :loading="batchLaunchingEightD"
          @click="handleBatch8D"
        >
          批量发起8D
        </el-button>
      </div>

      <el-table
        v-loading="loading"
        :data="complaintList"
        stripe
        class="w-full"
        row-key="id"
        :row-class-name="getRowClassName"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="48" fixed="left" />
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
        <el-table-column label="实物解析" width="120">
          <template #default="{ row }">
            <el-tag
              v-if="row.requires_physical_analysis"
              :type="getCustomerComplaintPhysicalAnalysisStatusType(row.physical_analysis_status)"
            >
              {{ getCustomerComplaintPhysicalAnalysisStatusLabel(row.physical_analysis_status) }}
            </el-tag>
            <el-tag v-else type="success">免解析</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="实物处理" width="110">
          <template #default="{ row }">
            <span v-if="row.requires_physical_analysis" class="text-gray-400">-</span>
            <el-tag v-else :type="getCustomerComplaintDispositionStatusType(row.physical_disposition_status)">
              {{ getCustomerComplaintDispositionStatusLabel(row.physical_disposition_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="8D状态" width="140">
          <template #default="{ row }">
            <el-tag v-if="row.eight_d_report_id" type="primary">
              {{ getEightDDisplayStatus(row) }}
            </el-tag>
            <span v-else class="text-gray-400">未发起</span>
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
        <el-table-column label="操作" width="320" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleView(row)">查看</el-button>
            <el-button
              v-if="canHandleCustomerComplaintDisposition(row)"
              link
              type="primary"
              size="small"
              @click="handleDisposition(row)"
            >
              实物处理
            </el-button>
            <el-button
              v-if="canHandleCustomerComplaintAnalysis(row)"
              link
              type="primary"
              size="small"
              @click="handleAnalysis(row)"
            >
              实物解析
            </el-button>
            <el-button
              v-if="canOpenCustomerComplaintEightD(row)"
              link
              type="primary"
              size="small"
              :loading="launchingEightDId === row.id"
              @click="handle8D(row)"
            >
              {{ getEightDActionLabel(row) }}
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

    <CustomerComplaintDispositionDialog
      v-model="showDispositionDialog"
      :complaint="selectedComplaint"
      @success="handleDispositionSuccess"
    />

    <CustomerComplaintAnalysisDialog
      v-model="showAnalysisDialog"
      :complaint="selectedComplaint"
      @success="handleAnalysisSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  getCustomerComplaint,
  getCustomerComplaintCustomerOptions,
  getCustomerComplaints,
  initBatchCustomerComplaintEightD,
  initCustomerComplaintEightD,
} from '@/api/customer-quality'
import CustomerComplaintAnalysisDialog from '@/components/CustomerComplaintAnalysisDialog.vue'
import CustomerComplaintDispositionDialog from '@/components/CustomerComplaintDispositionDialog.vue'
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
  canBatchLaunchCustomerComplaintEightD,
  canHandleCustomerComplaintAnalysis,
  canHandleCustomerComplaintDisposition,
  canOpenCustomerComplaintEightD,
  getCustomerComplaintBatchLaunchHint,
  getCustomerComplaintEightDActionLabel,
  getCustomerComplaintDispositionStatusLabel,
  getCustomerComplaintDispositionStatusType,
  getCustomerComplaintPhysicalAnalysisStatusLabel,
  getCustomerComplaintPhysicalAnalysisStatusType,
  getCustomerComplaintStatusLabel,
  getCustomerComplaintStatusType,
} from '@/utils/customerComplaint'
import { getEightDStatusLabel } from '@/utils/customerEightD'

const route = useRoute()
const router = useRouter()
const problemManagementStore = useProblemManagementStore()

const loading = ref(false)
const complaintList = ref<CustomerComplaint[]>([])
const customerOptions = ref<CustomerComplaintCustomerOption[]>([])
const total = ref(0)
const showCreateDialog = ref(false)
const showDispositionDialog = ref(false)
const showAnalysisDialog = ref(false)
const selectedComplaint = ref<CustomerComplaint | null>(null)
const selectedComplaints = ref<CustomerComplaint[]>([])
const dateRange = ref<[string, string] | null>(null)
const launchingEightDId = ref<number | null>(null)
const batchLaunchingEightD = ref(false)

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
const canBatchLaunchEightD = computed(() =>
  canBatchLaunchCustomerComplaintEightD(selectedComplaints.value)
)
const focusedComplaintId = computed(() => parseFocusId(route.query.focusId))
const batchLaunchHint = computed(() =>
  getCustomerComplaintBatchLaunchHint(selectedComplaints.value)
)
const batchLaunchSummary = computed(() => {
  if (!selectedComplaints.value.length) {
    return '可勾选同一客户、同一客诉类型且已完成前置处理的客诉，批量发起同一张 8D。'
  }

  if (canBatchLaunchEightD.value) {
    return `已选择 ${selectedComplaints.value.length} 条客诉，可批量发起同一张 8D。`
  }

  return batchLaunchHint.value
})

const statusOptions = buildCustomerComplaintStatusOptions()

function getComplaintTypeLabel(complaintType: ComplaintType): string {
  return resolveCustomerComplaintTypeLabel(complaintType, problemManagementStore.getCategory)
}

function getEightDActionLabel(row: CustomerComplaint): string {
  return getCustomerComplaintEightDActionLabel(row)
}

function getEightDDisplayStatus(row: CustomerComplaint): string {
  return getEightDStatusLabel(row.eight_d_status)
}

function parseFocusId(value: unknown): number | null {
  const raw = Array.isArray(value) ? value[0] : value
  if (!raw) {
    return null
  }

  const parsed = Number(raw)
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null
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
    selectedComplaints.value = []
    total.value = response.total
    await loadFocusedComplaint()
  } catch (error: any) {
    ElMessage.error(error.message || '加载客诉列表失败')
    console.error('load complaints error:', error)
  } finally {
    loading.value = false
  }
}

async function loadFocusedComplaint() {
  if (
    !focusedComplaintId.value ||
    complaintList.value.some((item) => item.id === focusedComplaintId.value)
  ) {
    return
  }

  try {
    const focusedComplaint = await getCustomerComplaint(focusedComplaintId.value)
    complaintList.value = [focusedComplaint, ...complaintList.value]
  } catch (error) {
    console.error('Failed to load focused complaint:', error)
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
  router.push({
    name: 'CustomerComplaintDetail',
    params: { id: row.id },
    query: {
      sourceRouteName: 'CustomerComplaintList',
      sourceFocusId: String(row.id),
    },
  })
}

function handleDisposition(row: CustomerComplaint) {
  selectedComplaint.value = row
  showDispositionDialog.value = true
}

function handleAnalysis(row: CustomerComplaint) {
  selectedComplaint.value = row
  showAnalysisDialog.value = true
}

function handleSelectionChange(selection: CustomerComplaint[]) {
  selectedComplaints.value = selection
}

async function handle8D(row: CustomerComplaint) {
  if (row.eight_d_report_id) {
    router.push({
      name: 'EightDCustomerForm',
      params: { id: row.id },
      query: {
        sourceRouteName: 'CustomerComplaintList',
        sourceFocusId: String(row.id),
      },
    })
    return
  }

  try {
    launchingEightDId.value = row.id
    await initCustomerComplaintEightD(row.id)
    ElMessage.success(`客诉 ${row.complaint_number} 已发起 8D`)
    await loadComplaints()
    router.push({
      name: 'EightDCustomerForm',
      params: { id: row.id },
      query: {
        sourceRouteName: 'CustomerComplaintList',
        sourceFocusId: String(row.id),
      },
    })
  } catch (error: any) {
    ElMessage.error(error.message || '发起 8D 失败')
  } finally {
    launchingEightDId.value = null
  }
}

async function handleBatch8D() {
  const complaints = selectedComplaints.value
  const launchHint = getCustomerComplaintBatchLaunchHint(complaints)
  if (launchHint) {
    ElMessage.warning(launchHint)
    return
  }

  const primaryComplaint = complaints[0]
  if (!primaryComplaint) {
    ElMessage.warning('请先选择客诉记录')
    return
  }

  try {
    batchLaunchingEightD.value = true
    const report = await initBatchCustomerComplaintEightD({
      complaint_ids: complaints.map((item) => item.id),
      primary_complaint_id: primaryComplaint.id,
    })
    ElMessage.success(`已按 ${complaints.length} 条客诉发起同一张 8D`)
    await loadComplaints()
    router.push({
      name: 'EightDCustomerForm',
      params: { id: report.complaint_id || primaryComplaint.id },
      query: {
        sourceRouteName: 'CustomerComplaintList',
        sourceFocusId: String(report.complaint_id || primaryComplaint.id),
      },
    })
  } catch (error: any) {
    ElMessage.error(error.message || '批量发起 8D 失败')
  } finally {
    batchLaunchingEightD.value = false
  }
}

function handleCreateSuccess() {
  showCreateDialog.value = false
  ElMessage.success('客诉单创建成功')
  void loadComplaints()
}

function handleDispositionSuccess() {
  selectedComplaint.value = null
  void loadComplaints()
}

function handleAnalysisSuccess() {
  selectedComplaint.value = null
  void loadComplaints()
}

function getRowClassName({ row }: { row: CustomerComplaint }) {
  return focusedComplaintId.value === row.id ? 'focused-row' : ''
}

onMounted(() => {
  void problemManagementStore.loadCatalog()
  void loadCustomerOptions()
  void loadComplaints()
})

watch(
  () => route.query.focusId,
  async (current, previous) => {
    if (current === previous) {
      return
    }

    await loadComplaints()
  }
)
</script>

<style scoped>
.customer-complaint-list {
  min-height: 100vh;
}

:deep(.focused-row td) {
  background-color: #ecf5ff !important;
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
