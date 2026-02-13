<template>
  <div class="scar-list">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>SCAR 单据管理</h2>
      <el-button 
        v-if="canCreate" 
        type="primary" 
        @click="showCreateDialog = true"
      >
        <el-icon><Plus /></el-icon>
        创建 SCAR
      </el-button>
    </div>

    <!-- 筛选条件 -->
    <el-card class="filter-card" shadow="never">
      <el-form :model="filterForm" inline>
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="全部" clearable>
            <el-option label="待处理" value="pending" />
            <el-option label="进行中" value="in_progress" />
            <el-option label="已提交" value="submitted" />
            <el-option label="已批准" value="approved" />
            <el-option label="已驳回" value="rejected" />
            <el-option label="已关闭" value="closed" />
          </el-select>
        </el-form-item>

        <el-form-item label="严重度">
          <el-select v-model="filterForm.severity" placeholder="全部" clearable>
            <el-option label="严重" value="critical" />
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>

        <el-form-item label="开始日期">
          <el-date-picker
            v-model="filterForm.start_date"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item label="结束日期">
          <el-date-picker
            v-model="filterForm.end_date"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            查询
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- SCAR 列表 -->
    <el-card class="table-card" shadow="never">
      <el-table 
        v-loading="loading"
        :data="scarList" 
        stripe
        @row-click="handleRowClick"
        style="cursor: pointer;"
      >
        <el-table-column prop="scar_number" label="单据编号" width="150" fixed />
        <el-table-column prop="supplier_name" label="供应商" width="150" />
        <el-table-column prop="material_code" label="物料编码" width="120" />
        <el-table-column prop="defect_description" label="缺陷描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="defect_qty" label="不良数量" width="100" align="right" />
        <el-table-column prop="severity" label="严重度" width="100">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)" size="small">
              {{ getSeverityLabel(row.severity) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="deadline" label="截止日期" width="120">
          <template #default="{ row }">
            <span :class="{ 'text-danger': isOverdue(row.deadline) }">
              {{ formatDate(row.deadline) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="current_handler_name" label="当前处理人" width="100" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click.stop="handleView(row)">
              查看
            </el-button>
            <el-button 
              v-if="canSubmit8D(row)" 
              type="success" 
              size="small" 
              @click.stop="handleSubmit8D(row)"
            >
              提交8D
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 创建 SCAR 对话框（仅内部用户） -->
    <el-dialog
      v-model="showCreateDialog"
      title="创建 SCAR 单据"
      width="600px"
    >
      <el-form :model="createForm" :rules="createRules" ref="createFormRef" label-width="120px">
        <el-form-item label="供应商" prop="supplier_id">
          <el-select v-model="createForm.supplier_id" placeholder="请选择供应商" filterable>
            <el-option 
              v-for="supplier in suppliers" 
              :key="supplier.id" 
              :label="supplier.name" 
              :value="supplier.id" 
            />
          </el-select>
        </el-form-item>

        <el-form-item label="物料编码" prop="material_code">
          <el-input v-model="createForm.material_code" placeholder="请输入物料编码" />
        </el-form-item>

        <el-form-item label="缺陷描述" prop="defect_description">
          <el-input 
            v-model="createForm.defect_description" 
            type="textarea" 
            :rows="4"
            placeholder="请详细描述缺陷情况"
          />
        </el-form-item>

        <el-form-item label="不良数量" prop="defect_qty">
          <el-input-number v-model="createForm.defect_qty" :min="1" />
        </el-form-item>

        <el-form-item label="严重度" prop="severity">
          <el-select v-model="createForm.severity" placeholder="请选择严重度">
            <el-option label="严重" value="critical" />
            <el-option label="高" value="high" />
            <el-option label="中" value="medium" />
            <el-option label="低" value="low" />
          </el-select>
        </el-form-item>

        <el-form-item label="截止日期" prop="deadline">
          <el-date-picker
            v-model="createForm.deadline"
            type="datetime"
            placeholder="选择截止日期"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate" :loading="creating">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { supplierApi } from '@/api/supplier'
import { useAuthStore } from '@/stores/auth'
import type { SCAR, SCARListParams } from '@/types/supplier'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const creating = ref(false)
const showCreateDialog = ref(false)
const scarList = ref<SCAR[]>([])
const suppliers = ref<any[]>([])

// 筛选表单
const filterForm = reactive<SCARListParams>({
  status: undefined,
  severity: undefined,
  start_date: undefined,
  end_date: undefined
})

// 分页
const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0
})

// 创建表单
const createForm = reactive<any>({
  supplier_id: undefined,
  material_code: '',
  defect_description: '',
  defect_qty: 1,
  severity: 'medium',
  deadline: ''
})

const createFormRef = ref()

// 创建表单验证规则
const createRules = {
  supplier_id: [{ required: true, message: '请选择供应商', trigger: 'change' }],
  material_code: [{ required: true, message: '请输入物料编码', trigger: 'blur' }],
  defect_description: [{ required: true, message: '请输入缺陷描述', trigger: 'blur' }],
  defect_qty: [{ required: true, message: '请输入不良数量', trigger: 'blur' }],
  severity: [{ required: true, message: '请选择严重度', trigger: 'change' }],
  deadline: [{ required: true, message: '请选择截止日期', trigger: 'change' }]
}

// 是否可以创建（仅内部用户）
const canCreate = computed(() => authStore.isInternal)

// 是否可以提交8D（供应商用户且状态为待处理或进行中）
const canSubmit8D = (row: SCAR) => {
  return authStore.isSupplier && ['pending', 'in_progress'].includes(row.status)
}

// 获取严重度类型
const getSeverityType = (severity: string) => {
  switch (severity) {
    case 'critical': return 'danger'
    case 'high': return 'warning'
    case 'medium': return 'primary'
    default: return 'info'
  }
}

// 获取严重度标签
const getSeverityLabel = (severity: string) => {
  const labels: Record<string, string> = {
    critical: '严重',
    high: '高',
    medium: '中',
    low: '低'
  }
  return labels[severity] || severity
}

// 获取状态类型
const getStatusType = (status: string) => {
  switch (status) {
    case 'closed': return 'success'
    case 'approved': return 'success'
    case 'rejected': return 'danger'
    case 'in_progress': return 'warning'
    default: return 'info'
  }
}

// 获取状态标签
const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    pending: '待处理',
    in_progress: '进行中',
    submitted: '已提交',
    approved: '已批准',
    rejected: '已驳回',
    closed: '已关闭'
  }
  return labels[status] || status
}

// 格式化日期
const formatDate = (date: string) => {
  if (!date) return ''
  return new Date(date).toLocaleDateString('zh-CN')
}

// 判断是否逾期
const isOverdue = (deadline: string) => {
  if (!deadline) return false
  return new Date(deadline) < new Date()
}

// 加载 SCAR 列表
const loadSCARList = async () => {
  try {
    loading.value = true
    const params: SCARListParams = {
      page: pagination.page,
      page_size: pagination.page_size,
      ...filterForm
    }
    const response = await supplierApi.getSCARList(params)
    scarList.value = response.items
    pagination.total = response.total
  } catch (error) {
    console.error('Failed to load SCAR list:', error)
    ElMessage.error('加载 SCAR 列表失败')
  } finally {
    loading.value = false
  }
}

// 查询
const handleSearch = () => {
  pagination.page = 1
  loadSCARList()
}

// 重置
const handleReset = () => {
  Object.assign(filterForm, {
    status: undefined,
    severity: undefined,
    start_date: undefined,
    end_date: undefined
  })
  handleSearch()
}

// 分页大小变化
const handleSizeChange = () => {
  pagination.page = 1
  loadSCARList()
}

// 页码变化
const handlePageChange = () => {
  loadSCARList()
}

// 行点击
const handleRowClick = (row: SCAR) => {
  handleView(row)
}

// 查看详情
const handleView = (row: SCAR) => {
  router.push(`/supplier/scar/${row.id}`)
}

// 提交8D
const handleSubmit8D = (row: SCAR) => {
  router.push(`/supplier/scar/${row.id}/8d`)
}

// 创建 SCAR
const handleCreate = async () => {
  try {
    await createFormRef.value.validate()
    creating.value = true
    await supplierApi.createSCAR(createForm)
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    loadSCARList()
  } catch (error) {
    console.error('Failed to create SCAR:', error)
    if (error !== false) { // 不是表单验证错误
      ElMessage.error('创建失败')
    }
  } finally {
    creating.value = false
  }
}

onMounted(() => {
  loadSCARList()
})
</script>

<style scoped lang="scss">
.scar-list {
  padding: 20px;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    h2 {
      margin: 0;
      font-size: 24px;
      font-weight: 600;
    }
  }

  .filter-card {
    margin-bottom: 20px;
  }

  .table-card {
    .pagination-container {
      margin-top: 20px;
      display: flex;
      justify-content: flex-end;
    }
  }

  .text-danger {
    color: #f56c6c;
  }

  // 响应式布局
  @media (max-width: 768px) {
    padding: 10px;

    .page-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 10px;

      h2 {
        font-size: 20px;
      }
    }
  }
}
</style>
