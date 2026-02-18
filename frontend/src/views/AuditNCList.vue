<template>
  <div class="audit-nc-list p-4 md:p-6">
    <div class="mb-6">
      <h1 class="text-2xl font-bold">NC整改清单</h1>
      <p class="text-sm text-gray-500 mt-1">Audit NC List - 审核不符合项整改跟踪</p>
    </div>

    <!-- 筛选 -->
    <el-card class="mb-6">
      <el-form :inline="true" :model="queryForm">
        <el-form-item label="验证状态">
          <el-select v-model="queryForm.verification_status" placeholder="全部" clearable>
            <el-option label="待指派" value="pending" />
            <el-option label="已指派" value="assigned" />
            <el-option label="已响应" value="responded" />
            <el-option label="已验证" value="verified" />
            <el-option label="已关闭" value="closed" />
          </el-select>
        </el-form-item>
        <el-form-item label="是否逾期">
          <el-select v-model="queryForm.is_overdue" placeholder="全部" clearable>
            <el-option label="是" :value="true" />
            <el-option label="否" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadNCs">查询</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- NC列表 -->
    <el-card v-loading="loading">
      <el-table :data="ncs" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="nc_item" label="条款" width="120" />
        <el-table-column prop="nc_description" label="不符合项描述" min-width="250" show-overflow-tooltip />
        <el-table-column prop="responsible_dept" label="责任部门" width="120" />
        
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.verification_status)">
              {{ getStatusLabel(row.verification_status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="期限" width="180">
          <template #default="{ row }">
            <div :class="row.is_overdue ? 'text-red-600 font-bold' : ''">
              {{ formatDateTime(row.deadline) }}
              <el-tag v-if="row.is_overdue" type="danger" size="small" class="ml-1">
                逾期
              </el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.verification_status === 'pending'"
              link
              type="primary"
              @click="handleAssign(row)"
            >
              指派
            </el-button>
            <el-button
              v-if="row.verification_status === 'assigned'"
              link
              type="primary"
              @click="handleRespond(row)"
            >
              填写对策
            </el-button>
            <el-button
              v-if="row.verification_status === 'responded'"
              link
              type="success"
              @click="handleVerify(row)"
            >
              验证
            </el-button>
            <el-button
              v-if="row.verification_status === 'verified'"
              link
              type="success"
              @click="handleClose(row)"
            >
              关闭
            </el-button>
            <el-button link @click="handleView(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="mt-4 flex justify-end">
        <el-pagination
          v-model:current-page="queryForm.page"
          v-model:page-size="queryForm.page_size"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="loadNCs"
        />
      </div>
    </el-card>

    <!-- 指派对话框 -->
    <el-dialog v-model="showAssignDialog" title="指派NC" width="500px">
      <el-form :model="assignForm" label-width="100px">
        <el-form-item label="指派给">
          <el-input-number v-model="assignForm.assigned_to" :min="1" placeholder="用户ID" class="w-full" />
        </el-form-item>
        <el-form-item label="整改期限">
          <el-date-picker
            v-model="assignForm.deadline"
            type="datetime"
            placeholder="选择期限"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DDTHH:mm:ss"
            class="w-full"
          />
        </el-form-item>
        <el-form-item label="指派说明">
          <el-input v-model="assignForm.comment" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAssignDialog = false">取消</el-button>
        <el-button type="primary" @click="submitAssign" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>

    <!-- 响应对话框 -->
    <el-dialog v-model="showRespondDialog" title="填写整改对策" width="600px">
      <el-form :model="respondForm" label-width="100px">
        <el-form-item label="根本原因" required>
          <el-input v-model="respondForm.root_cause" type="textarea" :rows="4" placeholder="请详细分析根本原因" />
        </el-form-item>
        <el-form-item label="纠正措施" required>
          <el-input v-model="respondForm.corrective_action" type="textarea" :rows="4" placeholder="请详细说明纠正措施" />
        </el-form-item>
        <el-form-item label="整改证据">
          <el-input v-model="respondForm.corrective_evidence" placeholder="证据文件路径" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRespondDialog = false">取消</el-button>
        <el-button type="primary" @click="submitRespond" :loading="submitting">提交</el-button>
      </template>
    </el-dialog>

    <!-- 验证对话框 -->
    <el-dialog v-model="showVerifyDialog" title="验证NC整改" width="500px">
      <el-form :model="verifyForm" label-width="100px">
        <el-form-item label="验证结果" required>
          <el-radio-group v-model="verifyForm.is_approved">
            <el-radio :label="true">验证通过</el-radio>
            <el-radio :label="false">验证不通过</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="验证意见" required>
          <el-input v-model="verifyForm.verification_comment" type="textarea" :rows="4" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showVerifyDialog = false">取消</el-button>
        <el-button type="primary" @click="submitVerify" :loading="submitting">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import {
  getAuditNCs,
  assignAuditNC,
  respondAuditNC,
  verifyAuditNC,
  closeAuditNC
} from '@/api/audit';
import type { AuditNC, AuditNCAssign, AuditNCResponse, AuditNCVerify } from '@/types/audit';

const loading = ref(false);
const submitting = ref(false);
const ncs = ref<AuditNC[]>([]);
const total = ref(0);
const currentNC = ref<AuditNC | null>(null);

const showAssignDialog = ref(false);
const showRespondDialog = ref(false);
const showVerifyDialog = ref(false);

const queryForm = reactive({
  verification_status: '',
  is_overdue: undefined as boolean | undefined,
  page: 1,
  page_size: 20
});

const assignForm = reactive<AuditNCAssign>({
  assigned_to: 0,
  deadline: '',
  comment: ''
});

const respondForm = reactive<AuditNCResponse>({
  root_cause: '',
  corrective_action: '',
  corrective_evidence: ''
});

const verifyForm = reactive<AuditNCVerify>({
  is_approved: true,
  verification_comment: ''
});

const loadNCs = async () => {
  loading.value = true;
  try {
    const response = await getAuditNCs(queryForm);
    ncs.value = response.items;
    total.value = response.total;
  } catch (error: any) {
    ElMessage.error(error.message || '加载失败');
  } finally {
    loading.value = false;
  }
};

const handleAssign = (nc: AuditNC) => {
  currentNC.value = nc;
  Object.assign(assignForm, { assigned_to: 0, deadline: '', comment: '' });
  showAssignDialog.value = true;
};

const submitAssign = async () => {
  if (!currentNC.value) return;
  submitting.value = true;
  try {
    await assignAuditNC(currentNC.value.id, assignForm);
    ElMessage.success('指派成功');
    showAssignDialog.value = false;
    await loadNCs();
  } catch (error: any) {
    ElMessage.error(error.message || '指派失败');
  } finally {
    submitting.value = false;
  }
};

const handleRespond = (nc: AuditNC) => {
  currentNC.value = nc;
  Object.assign(respondForm, { root_cause: '', corrective_action: '', corrective_evidence: '' });
  showRespondDialog.value = true;
};

const submitRespond = async () => {
  if (!currentNC.value) return;
  submitting.value = true;
  try {
    await respondAuditNC(currentNC.value.id, respondForm);
    ElMessage.success('提交成功');
    showRespondDialog.value = false;
    await loadNCs();
  } catch (error: any) {
    ElMessage.error(error.message || '提交失败');
  } finally {
    submitting.value = false;
  }
};

const handleVerify = (nc: AuditNC) => {
  currentNC.value = nc;
  Object.assign(verifyForm, { is_approved: true, verification_comment: '' });
  showVerifyDialog.value = true;
};

const submitVerify = async () => {
  if (!currentNC.value) return;
  submitting.value = true;
  try {
    await verifyAuditNC(currentNC.value.id, verifyForm);
    ElMessage.success('验证成功');
    showVerifyDialog.value = false;
    await loadNCs();
  } catch (error: any) {
    ElMessage.error(error.message || '验证失败');
  } finally {
    submitting.value = false;
  }
};

const handleClose = async (nc: AuditNC) => {
  try {
    await closeAuditNC(nc.id);
    ElMessage.success('关闭成功');
    await loadNCs();
  } catch (error: any) {
    ElMessage.error(error.message || '关闭失败');
  }
};

const handleView = (_nc: AuditNC) => {
  ElMessage.info('查看NC详情');
};

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    pending: '待指派',
    assigned: '已指派',
    responded: '已响应',
    verified: '已验证',
    rejected: '已驳回',
    closed: '已关闭'
  };
  return labels[status] || status;
};

const getStatusType = (status: string) => {
  const types: Record<string, any> = {
    pending: 'info',
    assigned: 'warning',
    responded: 'primary',
    verified: 'success',
    rejected: 'danger',
    closed: 'success'
  };
  return types[status] || 'info';
};

const formatDateTime = (dateStr: string): string => {
  return new Date(dateStr).toLocaleString('zh-CN');
};

onMounted(() => {
  loadNCs();
});
</script>

<style scoped>
.audit-nc-list {
  min-height: 100vh;
  background-color: #f5f7fa;
}
</style>
