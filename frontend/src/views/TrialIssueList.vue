<template>
  <div class="trial-issue-list p-4 md:p-6">
    <div class="header mb-6">
      <h1 class="text-2xl font-bold mb-2">试产问题清单</h1>
      <p class="text-gray-600">管理试产过程中发现的问题及闭环跟踪</p>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4" v-if="statistics">
      <el-card>
        <div class="text-center">
          <div class="text-3xl font-bold text-blue-600">{{ statistics.total_issues }}</div>
          <div class="text-gray-600 mt-2">问题总数</div>
        </div>
      </el-card>
      <el-card>
        <div class="text-center">
          <div class="text-3xl font-bold text-orange-600">{{ statistics.open_issues + statistics.in_progress_issues }}</div>
          <div class="text-gray-600 mt-2">待处理</div>
        </div>
      </el-card>
      <el-card>
        <div class="text-center">
          <div class="text-3xl font-bold text-green-600">{{ statistics.resolved_issues }}</div>
          <div class="text-gray-600 mt-2">已解决</div>
        </div>
      </el-card>
      <el-card>
        <div class="text-center">
          <div class="text-3xl font-bold text-red-600">{{ statistics.legacy_issues }}</div>
          <div class="text-gray-600 mt-2">遗留问题</div>
        </div>
      </el-card>
    </div>

    <!-- 搜索和筛选 -->
    <el-card class="mb-4">
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="问题类型">
          <el-select v-model="searchForm.issue_type" placeholder="全部" clearable class="w-full md:w-32">
            <el-option label="设计" value="design" />
            <el-option label="模具" value="tooling" />
            <el-option label="工艺" value="process" />
            <el-option label="物料" value="material" />
            <el-option label="设备" value="equipment" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="全部" clearable class="w-full md:w-32">
            <el-option label="待处理" value="open" />
            <el-option label="处理中" value="in_progress" />
            <el-option label="已解决" value="resolved" />
            <el-option label="已关闭" value="closed" />
            <el-option label="已升级" value="escalated" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button type="success" @click="handleCreate">录入问题</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 问题列表 -->
    <el-card>
      <el-table :data="issueList" v-loading="loading" stripe>
        <el-table-column prop="issue_number" label="问题编号" width="140" />
        <el-table-column prop="issue_description" label="问题描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="issue_type" label="问题类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getIssueTypeType(row.issue_type)" size="small">
              {{ getIssueTypeLabel(row.issue_type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="assigned_dept" label="责任部门" width="120" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_legacy_issue" label="遗留问题" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_legacy_issue" type="danger" size="small">遗留</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="deadline" label="截止日期" width="120">
          <template #default="{ row }">
            <span :class="isOverdue(row.deadline) ? 'text-red-600' : ''">
              {{ formatDate(row.deadline, 'date') }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleView(row)">查看</el-button>
            <el-button
              v-if="row.status === 'open' || row.status === 'in_progress'"
              link
              type="success"
              size="small"
              @click="handleSubmitSolution(row)"
            >
              提交方案
            </el-button>
            <el-button
              v-if="row.status === 'resolved'"
              link
              type="warning"
              size="small"
              @click="handleClose(row)"
            >
              关闭
            </el-button>
            <el-button
              v-if="!row.is_escalated_to_8d"
              link
              type="danger"
              size="small"
              @click="handleEscalate(row)"
            >
              升级8D
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination mt-4 flex justify-end">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSearch"
          @current-change="handleSearch"
        />
      </div>
    </el-card>

    <!-- 创建问题对话框 -->
    <el-dialog v-model="dialogVisible" title="录入试产问题" width="600px" :close-on-click-modal="false">
      <el-form :model="formData" :rules="formRules" ref="formRef" label-width="120px">
        <el-form-item label="问题描述" prop="issue_description">
          <el-input v-model="formData.issue_description" type="textarea" :rows="3" placeholder="请详细描述问题" />
        </el-form-item>
        <el-form-item label="问题类型" prop="issue_type">
          <el-select v-model="formData.issue_type" placeholder="请选择问题类型" class="w-full">
            <el-option label="设计问题" value="design" />
            <el-option label="模具问题" value="tooling" />
            <el-option label="工艺问题" value="process" />
            <el-option label="物料问题" value="material" />
            <el-option label="设备问题" value="equipment" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="责任部门" prop="assigned_dept">
          <el-input v-model="formData.assigned_dept" placeholder="请输入责任部门" />
        </el-form-item>
        <el-form-item label="要求完成时间" prop="deadline">
          <el-date-picker v-model="formData.deadline" type="datetime" placeholder="选择截止时间" class="w-full" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 提交解决方案对话框 -->
    <el-dialog v-model="solutionDialogVisible" title="提交解决方案" width="600px">
      <el-form :model="solutionForm" ref="solutionFormRef" label-width="120px">
        <el-form-item label="根本原因" prop="root_cause">
          <el-input v-model="solutionForm.root_cause" type="textarea" :rows="3" placeholder="请描述根本原因" />
        </el-form-item>
        <el-form-item label="解决方案" prop="solution">
          <el-input v-model="solutionForm.solution" type="textarea" :rows="3" placeholder="请描述解决方案" />
        </el-form-item>
        <el-form-item label="验证方法" prop="verification_method">
          <el-input v-model="solutionForm.verification_method" type="textarea" :rows="2" placeholder="请描述验证方法" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="solutionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitSolutionForm" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 查看详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="问题详情" width="700px">
      <el-descriptions :column="1" border v-if="currentIssue">
        <el-descriptions-item label="问题编号">{{ currentIssue.issue_number }}</el-descriptions-item>
        <el-descriptions-item label="问题描述">
          <div class="whitespace-pre-wrap">{{ currentIssue.issue_description }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="问题类型">
          <el-tag :type="getIssueTypeType(currentIssue.issue_type)">
            {{ getIssueTypeLabel(currentIssue.issue_type) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="责任部门">{{ currentIssue.assigned_dept || '-' }}</el-descriptions-item>
        <el-descriptions-item label="根本原因" v-if="currentIssue.root_cause">
          <div class="whitespace-pre-wrap">{{ currentIssue.root_cause }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="解决方案" v-if="currentIssue.solution">
          <div class="whitespace-pre-wrap">{{ currentIssue.solution }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="验证方法" v-if="currentIssue.verification_method">
          <div class="whitespace-pre-wrap">{{ currentIssue.verification_method }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentIssue.status)">
            {{ getStatusLabel(currentIssue.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="截止日期">{{ formatDate(currentIssue.deadline || '', 'date') }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(currentIssue.created_at) }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { newProductApi } from '@/api/new-product'
import type { TrialIssue, TrialIssueCreate, TrialIssueStatistics } from '@/types/new-product'

const route = useRoute()

// 数据状态
const loading = ref(false)
const submitting = ref(false)
const issueList = ref<TrialIssue[]>([])
const statistics = ref<TrialIssueStatistics | null>(null)
const pagination = reactive({ page: 1, page_size: 20, total: 0 })

// 搜索表单
const searchForm = reactive({
  trial_id: route.query.trial_id ? Number(route.query.trial_id) : undefined,
  issue_type: '',
  status: ''
})

// 对话框状态
const dialogVisible = ref(false)
const solutionDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const currentIssue = ref<TrialIssue | null>(null)

// 表单
const formRef = ref<FormInstance>()
const formData = reactive<TrialIssueCreate>({
  trial_id: searchForm.trial_id || 0,
  issue_description: '',
  issue_type: 'process',
  assigned_dept: '',
  deadline: ''
})
const solutionForm = reactive({
  root_cause: '',
  solution: '',
  verification_method: ''
})

const formRules: FormRules = {
  issue_description: [{ required: true, message: '请输入问题描述', trigger: 'blur' }],
  issue_type: [{ required: true, message: '请选择问题类型', trigger: 'change' }]
}

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.page_size,
      trial_id: searchForm.trial_id,
      issue_type: searchForm.issue_type || undefined,
      status: searchForm.status || undefined
    }
    const response = await newProductApi.getTrialIssueList(params)
    issueList.value = response.items
    pagination.total = response.total
  } catch (error: any) {
    ElMessage.error(error.message || '加载数据失败')
  } finally {
    loading.value = false
  }
}

// 加载统计
const loadStatistics = async () => {
  if (!searchForm.trial_id) return
  try {
    statistics.value = await newProductApi.getTrialIssueStatistics(searchForm.trial_id)
  } catch (error: any) {
    ElMessage.error(error.message || '加载统计失败')
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  loadData()
}

// 重置
const handleReset = () => {
  searchForm.issue_type = ''
  searchForm.status = ''
  handleSearch()
}

// 创建
const handleCreate = () => {
  Object.assign(formData, {
    trial_id: searchForm.trial_id || 0,
    issue_description: '',
    issue_type: 'process',
    assigned_dept: '',
    deadline: ''
  })
  dialogVisible.value = true
}

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    submitting.value = true
    
    const submitData = {
      ...formData,
      deadline: formData.deadline ? new Date(formData.deadline).toISOString() : undefined
    }
    
    await newProductApi.createTrialIssue(submitData)
    ElMessage.success('创建成功')
    dialogVisible.value = false
    loadData()
    loadStatistics()
  } catch (error: any) {
    if (error !== false) {
      ElMessage.error(error.message || '操作失败')
    }
  } finally {
    submitting.value = false
  }
}

// 查看详情
const handleView = (row: TrialIssue) => {
  currentIssue.value = row
  detailDialogVisible.value = true
}

// 提交解决方案
const handleSubmitSolution = (row: TrialIssue) => {
  currentIssue.value = row
  Object.assign(solutionForm, {
    root_cause: row.root_cause || '',
    solution: row.solution || '',
    verification_method: row.verification_method || ''
  })
  solutionDialogVisible.value = true
}

// 提交解决方案表单
const handleSubmitSolutionForm = async () => {
  if (!currentIssue.value) return
  submitting.value = true
  try {
    await newProductApi.submitSolution(currentIssue.value.id, solutionForm)
    ElMessage.success('提交成功')
    solutionDialogVisible.value = false
    loadData()
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

// 关闭问题
const handleClose = async (row: TrialIssue) => {
  try {
    await ElMessageBox.confirm('确定要关闭这个问题吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await newProductApi.closeIssue(row.id)
    ElMessage.success('关闭成功')
    loadData()
    loadStatistics()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '操作失败')
    }
  }
}

// 升级为8D
const handleEscalate = async (row: TrialIssue) => {
  try {
    const result = await ElMessageBox.prompt('请输入升级原因', '升级为8D报告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /.+/,
      inputErrorMessage: '请输入升级原因'
    }) as { action: string; value: string }
    
    if (result.action === 'confirm' && result.value) {
      await newProductApi.escalateTo8D(row.id, { escalation_reason: result.value })
      ElMessage.success('升级成功')
      loadData()
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '操作失败')
    }
  }
}

// 辅助函数
const getIssueTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    design: '设计', tooling: '模具', process: '工艺',
    material: '物料', equipment: '设备', other: '其他'
  }
  return labels[type] || type
}

const getIssueTypeType = (type: string) => {
  const types: Record<string, any> = {
    design: 'primary', tooling: 'warning', process: 'success',
    material: 'danger', equipment: 'info', other: ''
  }
  return types[type] || ''
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    open: '待处理', in_progress: '处理中', resolved: '已解决',
    closed: '已关闭', escalated: '已升级'
  }
  return labels[status] || status
}

const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    open: 'danger', in_progress: 'warning', resolved: 'success',
    closed: 'info', escalated: 'primary'
  }
  return types[status] || ''
}

const isOverdue = (deadline: string) => {
  if (!deadline) return false
  return new Date(deadline) < new Date()
}

const formatDate = (dateStr: string, type: 'date' | 'datetime' = 'datetime') => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return type === 'date' ? date.toLocaleDateString('zh-CN') : date.toLocaleString('zh-CN')
}

// 初始化
onMounted(() => {
  loadData()
  loadStatistics()
})
</script>

<style scoped>
.trial-issue-list {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.search-form :deep(.el-form-item) {
  margin-bottom: 0;
}

@media (max-width: 768px) {
  .search-form {
    display: block;
  }
  
  .search-form :deep(.el-form-item) {
    display: block;
    margin-bottom: 12px;
  }
}
</style>
