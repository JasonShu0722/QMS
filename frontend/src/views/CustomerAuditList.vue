<template>
  <div class="customer-audit-list p-4 md:p-6">
    <div class="flex justify-between items-center mb-6">
      <div>
        <h1 class="text-2xl font-bold">客户审核台账</h1>
        <p class="text-sm text-gray-500 mt-1">Customer Audit List - 客户来厂审核记录管理</p>
      </div>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        创建客户审核记录
      </el-button>
    </div>

    <!-- 筛选 -->
    <el-card class="mb-6">
      <el-form :inline="true" :model="queryForm">
        <el-form-item label="客户名称">
          <el-input v-model="queryForm.customer_name" placeholder="模糊搜索" clearable />
        </el-form-item>
        <el-form-item label="审核类型">
          <el-select v-model="queryForm.audit_type" placeholder="全部" clearable>
            <el-option label="体系审核" value="system" />
            <el-option label="过程审核" value="process" />
            <el-option label="产品审核" value="product" />
            <el-option label="资质审核" value="qualification" />
            <el-option label="潜在供应商" value="potential_supplier" />
          </el-select>
        </el-form-item>
        <el-form-item label="最终结果">
          <el-select v-model="queryForm.final_result" placeholder="全部" clearable>
            <el-option label="通过" value="passed" />
            <el-option label="有条件通过" value="conditional_passed" />
            <el-option label="未通过" value="failed" />
            <el-option label="待定" value="pending" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadAudits">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 列表 -->
    <el-card v-loading="loading">
      <el-table :data="audits" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="customer_name" label="客户名称" min-width="150" />
        
        <el-table-column label="审核类型" width="120">
          <template #default="{ row }">
            {{ getAuditTypeLabel(row.audit_type) }}
          </template>
        </el-table-column>

        <el-table-column prop="audit_date" label="审核日期" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.audit_date) }}
          </template>
        </el-table-column>

        <el-table-column label="最终结果" width="120">
          <template #default="{ row }">
            <el-tag :type="getResultType(row.final_result)">
              {{ getResultLabel(row.final_result) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="得分" width="100">
          <template #default="{ row }">
            <span v-if="row.score" class="font-bold">{{ row.score }}</span>
            <span v-else class="text-gray-400">-</span>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleView(row)">查看</el-button>
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="success" @click="handleCreateIssueTask(row)">
              创建问题任务
            </el-button>
            <el-button link type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="mt-4 flex justify-end">
        <el-pagination
          v-model:current-page="queryForm.page"
          v-model:page-size="queryForm.page_size"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="loadAudits"
        />
      </div>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="showFormDialog"
      :title="editingAudit ? '编辑客户审核' : '创建客户审核'"
      width="700px"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="120px">
        <el-form-item label="客户名称" prop="customer_name">
          <el-input v-model="form.customer_name" placeholder="请输入客户名称" />
        </el-form-item>

        <el-form-item label="审核类型" prop="audit_type">
          <el-select v-model="form.audit_type" placeholder="请选择" class="w-full">
            <el-option label="体系审核" value="system" />
            <el-option label="过程审核" value="process" />
            <el-option label="产品审核" value="product" />
            <el-option label="资质审核" value="qualification" />
            <el-option label="潜在供应商拜访" value="potential_supplier" />
          </el-select>
        </el-form-item>

        <el-form-item label="审核日期" prop="audit_date">
          <el-date-picker
            v-model="form.audit_date"
            type="datetime"
            placeholder="选择日期"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DDTHH:mm:ss"
            class="w-full"
          />
        </el-form-item>

        <el-form-item label="最终结果" prop="final_result">
          <el-select v-model="form.final_result" placeholder="请选择" class="w-full">
            <el-option label="通过" value="passed" />
            <el-option label="有条件通过" value="conditional_passed" />
            <el-option label="未通过" value="failed" />
            <el-option label="待定" value="pending" />
          </el-select>
        </el-form-item>

        <el-form-item label="审核得分" prop="score">
          <el-input-number v-model="form.score" :min="0" :max="100" class="w-full" />
        </el-form-item>

        <el-form-item label="内部接待人员" prop="internal_contact">
          <el-input v-model="form.internal_contact" placeholder="请输入接待人员" />
        </el-form-item>

        <el-form-item label="问题清单路径" prop="external_issue_list_path">
          <el-input v-model="form.external_issue_list_path" placeholder="客户提供的问题清单文件路径" />
        </el-form-item>

        <el-form-item label="审核报告路径" prop="audit_report_path">
          <el-input v-model="form.audit_report_path" placeholder="审核报告文件路径" />
        </el-form-item>

        <el-form-item label="审核总结" prop="summary">
          <el-input v-model="form.summary" type="textarea" :rows="4" placeholder="请输入审核总结" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showFormDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ editingAudit ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 创建问题任务对话框 -->
    <el-dialog v-model="showIssueTaskDialog" title="创建问题任务" width="600px">
      <el-form :model="issueTaskForm" label-width="120px">
        <el-form-item label="闂鍒嗙被">
          <el-tag type="info">{{ issueTaskProblemCategoryKey }} / {{ issueTaskProblemCategoryLabel }}</el-tag>
        </el-form-item>
        <el-form-item label="问题描述" required>
          <el-input v-model="issueTaskForm.issue_description" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="责任部门" required>
          <el-input v-model="issueTaskForm.responsible_dept" />
        </el-form-item>
        <el-form-item label="指派给">
          <el-input-number v-model="issueTaskForm.assigned_to" :min="1" class="w-full" />
        </el-form-item>
        <el-form-item label="整改期限" required>
          <el-date-picker
            v-model="issueTaskForm.deadline"
            type="datetime"
            placeholder="选择期限"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DDTHH:mm:ss"
            class="w-full"
          />
        </el-form-item>
        <el-form-item label="优先级">
          <el-select v-model="issueTaskForm.priority" class="w-full">
            <el-option label="低" value="low" />
            <el-option label="中" value="medium" />
            <el-option label="高" value="high" />
            <el-option label="紧急" value="critical" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showIssueTaskDialog = false">取消</el-button>
        <el-button type="primary" @click="submitIssueTask" :loading="submitting">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, reactive, onMounted } from 'vue';
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus';
import { Plus } from '@element-plus/icons-vue';
import {
  getCustomerAudits,
  createCustomerAudit,
  updateCustomerAudit,
  deleteCustomerAudit,
  createCustomerAuditIssueTask
} from '@/api/audit';
import type { CustomerAudit, CustomerAuditCreate, CustomerAuditIssueTaskCreate } from '@/types/audit';
import { useProblemManagementStore } from '@/stores/problemManagement';
import { getProblemCategoryLabel } from '@/utils/problemManagement';

const loading = ref(false);
const submitting = ref(false);
const audits = ref<CustomerAudit[]>([]);
const total = ref(0);
const showFormDialog = ref(false);
const showIssueTaskDialog = ref(false);
const editingAudit = ref<CustomerAudit | null>(null);
const currentAudit = ref<CustomerAudit | null>(null);
const problemManagementStore = useProblemManagementStore();
const issueTaskProblemCategoryKey = 'AQ3' as const;
const issueTaskProblemCategoryLabel = computed(() =>
  getProblemCategoryLabel(
    issueTaskProblemCategoryKey,
    '瀹㈡埛瀹℃牳闂',
    (categoryKey) => problemManagementStore.getCategory(categoryKey)
  )
);

const formRef = ref<FormInstance>();

const queryForm = reactive({
  customer_name: '',
  audit_type: '',
  final_result: '',
  page: 1,
  page_size: 20
});

const form = reactive<CustomerAuditCreate>({
  customer_name: '',
  audit_type: '',
  audit_date: '',
  final_result: '',
  score: undefined,
  internal_contact: '',
  external_issue_list_path: '',
  audit_report_path: '',
  summary: ''
});

const issueTaskForm = reactive<CustomerAuditIssueTaskCreate>({
  customer_audit_id: 0,
  issue_description: '',
  responsible_dept: '',
  assigned_to: undefined,
  deadline: '',
  priority: 'medium'
});

const formRules: FormRules = {
  customer_name: [{ required: true, message: '请输入客户名称', trigger: 'blur' }],
  audit_type: [{ required: true, message: '请选择审核类型', trigger: 'change' }],
  audit_date: [{ required: true, message: '请选择审核日期', trigger: 'change' }],
  final_result: [{ required: true, message: '请选择最终结果', trigger: 'change' }]
};

const loadAudits = async () => {
  loading.value = true;
  try {
    const response = await getCustomerAudits(queryForm);
    audits.value = response.items;
    total.value = response.total;
  } catch (error: any) {
    ElMessage.error(error.message || '加载失败');
  } finally {
    loading.value = false;
  }
};

const handleReset = () => {
  Object.assign(queryForm, {
    customer_name: '',
    audit_type: '',
    final_result: '',
    page: 1
  });
  loadAudits();
};

const handleCreate = () => {
  editingAudit.value = null;
  Object.assign(form, {
    customer_name: '',
    audit_type: '',
    audit_date: '',
    final_result: '',
    score: undefined,
    internal_contact: '',
    external_issue_list_path: '',
    audit_report_path: '',
    summary: ''
  });
  showFormDialog.value = true;
};

const handleEdit = (audit: CustomerAudit) => {
  editingAudit.value = audit;
  Object.assign(form, {
    customer_name: audit.customer_name,
    audit_type: audit.audit_type,
    audit_date: audit.audit_date,
    final_result: audit.final_result,
    score: audit.score,
    internal_contact: audit.internal_contact || '',
    external_issue_list_path: audit.external_issue_list_path || '',
    audit_report_path: audit.audit_report_path || '',
    summary: audit.summary || ''
  });
  showFormDialog.value = true;
};

const handleSubmit = async () => {
  if (!formRef.value) return;
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return;
    
    submitting.value = true;
    try {
      if (editingAudit.value) {
        await updateCustomerAudit(editingAudit.value.id, form);
        ElMessage.success('更新成功');
      } else {
        await createCustomerAudit(form);
        ElMessage.success('创建成功');
      }
      
      showFormDialog.value = false;
      await loadAudits();
    } catch (error: any) {
      ElMessage.error(error.message || '操作失败');
    } finally {
      submitting.value = false;
    }
  });
};

const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这条记录吗？', '确认删除', {
      type: 'warning'
    });
    
    await deleteCustomerAudit(id);
    ElMessage.success('删除成功');
    await loadAudits();
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败');
    }
  }
};

const handleCreateIssueTask = (audit: CustomerAudit) => {
  currentAudit.value = audit;
  Object.assign(issueTaskForm, {
    customer_audit_id: audit.id,
    issue_description: '',
    responsible_dept: '',
    assigned_to: undefined,
    deadline: '',
    priority: 'medium'
  });
  showIssueTaskDialog.value = true;
};

const submitIssueTask = async () => {
  submitting.value = true;
  try {
    await createCustomerAuditIssueTask(issueTaskForm);
    ElMessage.success('问题任务创建成功');
    showIssueTaskDialog.value = false;
  } catch (error: any) {
    ElMessage.error(error.message || '创建失败');
  } finally {
    submitting.value = false;
  }
};

const handleView = (_audit: CustomerAudit) => {
  ElMessage.info('查看详情功能');
};

const getAuditTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    system: '体系审核',
    process: '过程审核',
    product: '产品审核',
    qualification: '资质审核',
    potential_supplier: '潜在供应商'
  };
  return labels[type] || type;
};

const getResultLabel = (result: string): string => {
  const labels: Record<string, string> = {
    passed: '通过',
    conditional_passed: '有条件通过',
    failed: '未通过',
    pending: '待定'
  };
  return labels[result] || result;
};

const getResultType = (result: string) => {
  const types: Record<string, any> = {
    passed: 'success',
    conditional_passed: 'warning',
    failed: 'danger',
    pending: 'info'
  };
  return types[result] || 'info';
};

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    completed: '已完成',
    issue_open: '问题待关闭',
    issue_closed: '问题已关闭'
  };
  return labels[status] || status;
};

const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    completed: 'success',
    issue_open: 'warning',
    issue_closed: 'success'
  };
  return types[status] || 'info';
};

const formatDateTime = (dateStr: string): string => {
  return new Date(dateStr).toLocaleString('zh-CN');
};

onMounted(() => {
  void problemManagementStore.loadCatalog();
  loadAudits();
});
</script>

<style scoped>
.customer-audit-list {
  min-height: 100vh;
  background-color: #f5f7fa;
}
</style>
