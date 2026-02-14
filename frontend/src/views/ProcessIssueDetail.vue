<template>
  <div class="process-issue-detail">
    <!-- 返回按钮 -->
    <div class="mb-4">
      <el-button :icon="ArrowLeft" @click="handleBack">返回列表</el-button>
    </div>

    <el-card v-loading="loading">
      <!-- 问题单头部信息 -->
      <template #header>
        <div class="flex justify-between items-center">
          <div>
            <h2 class="text-xl font-bold">{{ issueDetail?.issue_number }}</h2>
            <div class="mt-2 flex items-center gap-4">
              <el-tag :type="getStatusTagType(issueDetail?.status)">
                {{ getStatusLabel(issueDetail?.status) }}
              </el-tag>
              <el-tag v-if="issueDetail?.is_overdue" type="danger">逾期</el-tag>
              <span class="text-sm text-gray-500">
                创建时间: {{ formatDateTime(issueDetail?.created_at) }}
              </span>
            </div>
          </div>
        </div>
      </template>

      <!-- 问题描述 -->
      <el-descriptions title="问题信息" :column="2" border class="mb-6">
        <el-descriptions-item label="问题描述" :span="2">
          <div class="whitespace-pre-wrap">{{ issueDetail?.issue_description }}</div>
        </el-descriptions-item>
        <el-descriptions-item label="责任类别">
          <el-tag :type="getResponsibilityTagType(issueDetail?.responsibility_category)">
            {{ getResponsibilityLabel(issueDetail?.responsibility_category) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="当前处理人">
          {{ issueDetail?.assigned_to }}
        </el-descriptions-item>
        <el-descriptions-item label="验证期">
          {{ issueDetail?.verification_period ? `${issueDetail.verification_period} 天` : '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="验证截止日期">
          {{ issueDetail?.verification_end_date || '-' }}
        </el-descriptions-item>
      </el-descriptions>

      <!-- 根本原因分析 -->
      <el-card v-if="issueDetail?.root_cause" class="mb-4" shadow="never">
        <template #header>
          <span class="font-semibold">根本原因分析</span>
        </template>
        <div class="whitespace-pre-wrap">{{ issueDetail.root_cause }}</div>
      </el-card>

      <!-- 围堵措施 -->
      <el-card v-if="issueDetail?.containment_action" class="mb-4" shadow="never">
        <template #header>
          <span class="font-semibold">围堵措施</span>
        </template>
        <div class="whitespace-pre-wrap">{{ issueDetail.containment_action }}</div>
      </el-card>

      <!-- 纠正措施 -->
      <el-card v-if="issueDetail?.corrective_action" class="mb-4" shadow="never">
        <template #header>
          <span class="font-semibold">纠正措施</span>
        </template>
        <div class="whitespace-pre-wrap">{{ issueDetail.corrective_action }}</div>
      </el-card>

      <!-- 改善证据 -->
      <el-card v-if="evidenceFiles.length > 0" class="mb-4" shadow="never">
        <template #header>
          <span class="font-semibold">改善证据</span>
        </template>
        <div class="evidence-list">
          <div v-for="(file, index) in evidenceFiles" :key="index" class="evidence-item">
            <el-link :href="file" target="_blank" type="primary">
              <el-icon><Document /></el-icon>
              {{ getFileName(file) }}
            </el-link>
          </div>
        </div>
      </el-card>

      <!-- 操作按钮区 -->
      <div class="action-buttons mt-6 flex gap-4">
        <!-- 填写对策（待处理状态） -->
        <el-button
          v-if="issueDetail?.status === 'open' && canRespond"
          type="primary"
          size="large"
          @click="showResponseDialog = true"
        >
          填写分析和对策
        </el-button>

        <!-- 验证对策（处理中状态） -->
        <el-button
          v-if="issueDetail?.status === 'in_progress' && canVerify"
          type="success"
          size="large"
          @click="showVerifyDialog = true"
        >
          验证对策有效性
        </el-button>

        <!-- 关闭问题单（验证中状态） -->
        <el-button
          v-if="issueDetail?.status === 'verifying' && canClose"
          type="warning"
          size="large"
          @click="showCloseDialog = true"
        >
          关闭问题单
        </el-button>
      </div>
    </el-card>

    <!-- 填写对策对话框 -->
    <el-dialog
      v-model="showResponseDialog"
      title="填写分析和对策"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="responseFormRef"
        :model="responseForm"
        :rules="responseRules"
        label-width="120px"
      >
        <el-form-item label="根本原因" prop="root_cause">
          <el-input
            v-model="responseForm.root_cause"
            type="textarea"
            :rows="4"
            placeholder="请详细描述根本原因分析（至少20字）"
            maxlength="2000"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="围堵措施" prop="containment_action">
          <el-input
            v-model="responseForm.containment_action"
            type="textarea"
            :rows="3"
            placeholder="请描述围堵措施（至少10字）"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="纠正措施" prop="corrective_action">
          <el-input
            v-model="responseForm.corrective_action"
            type="textarea"
            :rows="4"
            placeholder="请描述纠正措施（至少20字）"
            maxlength="2000"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="验证期" prop="verification_period">
          <el-input-number
            v-model="responseForm.verification_period"
            :min="1"
            :max="90"
            placeholder="请输入验证期天数"
          />
          <span class="ml-2 text-sm text-gray-500">天</span>
        </el-form-item>

        <el-form-item label="改善证据">
          <el-input
            v-model="evidenceInput"
            placeholder="请输入证据文件路径（多个路径用逗号分隔）"
          />
          <div class="text-xs text-gray-500 mt-1">
            示例: /uploads/evidence/photo1.jpg, /uploads/evidence/report.pdf
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showResponseDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitResponse" :loading="submitting">
          提交
        </el-button>
      </template>
    </el-dialog>

    <!-- 验证对策对话框 -->
    <el-dialog
      v-model="showVerifyDialog"
      title="验证对策有效性"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="verifyFormRef"
        :model="verifyForm"
        :rules="verifyRules"
        label-width="120px"
      >
        <el-form-item label="验证结果" prop="verification_result">
          <el-radio-group v-model="verifyForm.verification_result">
            <el-radio :label="true">有效</el-radio>
            <el-radio :label="false">无效</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="验证意见">
          <el-input
            v-model="verifyForm.verification_comments"
            type="textarea"
            :rows="4"
            placeholder="请输入验证意见（可选）"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showVerifyDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitVerify" :loading="submitting">
          提交
        </el-button>
      </template>
    </el-dialog>

    <!-- 关闭问题单对话框 -->
    <el-dialog
      v-model="showCloseDialog"
      title="关闭问题单"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="closeForm" label-width="120px">
        <el-form-item label="关闭备注">
          <el-input
            v-model="closeForm.close_comments"
            type="textarea"
            :rows="4"
            placeholder="请输入关闭备注（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCloseDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitClose" :loading="submitting">
          确认关闭
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import { ArrowLeft, Document } from '@element-plus/icons-vue';
import {
  getProcessIssue,
  respondToProcessIssue,
  verifyProcessIssue,
  closeProcessIssue
} from '@/api/process-quality';
import type {
  ProcessIssue,
  ProcessIssueStatus,
  ProcessIssueResponse,
  ProcessIssueVerification,
  ProcessIssueClose,
  ResponsibilityCategory
} from '@/types/process-quality';
import { useAuthStore } from '@/stores/auth';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

// 状态
const loading = ref(false);
const submitting = ref(false);
const issueDetail = ref<ProcessIssue | null>(null);
const showResponseDialog = ref(false);
const showVerifyDialog = ref(false);
const showCloseDialog = ref(false);
const evidenceInput = ref('');

// 表单引用
const responseFormRef = ref<FormInstance>();
const verifyFormRef = ref<FormInstance>();

// 填写对策表单
const responseForm = reactive<ProcessIssueResponse>({
  root_cause: '',
  containment_action: '',
  corrective_action: '',
  verification_period: 7,
  evidence_files: []
});

// 验证对策表单
const verifyForm = reactive<ProcessIssueVerification>({
  verification_result: true,
  verification_comments: ''
});

// 关闭问题单表单
const closeForm = reactive<ProcessIssueClose>({
  close_comments: ''
});

// 表单验证规则
const responseRules: FormRules = {
  root_cause: [
    { required: true, message: '请输入根本原因分析', trigger: 'blur' },
    { min: 20, max: 2000, message: '根本原因分析长度在 20 到 2000 个字符', trigger: 'blur' }
  ],
  containment_action: [
    { required: true, message: '请输入围堵措施', trigger: 'blur' },
    { min: 10, max: 1000, message: '围堵措施长度在 10 到 1000 个字符', trigger: 'blur' }
  ],
  corrective_action: [
    { required: true, message: '请输入纠正措施', trigger: 'blur' },
    { min: 20, max: 2000, message: '纠正措施长度在 20 到 2000 个字符', trigger: 'blur' }
  ],
  verification_period: [
    { required: true, message: '请输入验证期', trigger: 'blur' },
    { type: 'number', min: 1, max: 90, message: '验证期必须在 1 到 90 天之间', trigger: 'blur' }
  ]
};

const verifyRules: FormRules = {
  verification_result: [
    { required: true, message: '请选择验证结果', trigger: 'change' }
  ]
};

// 计算属性
const evidenceFiles = computed(() => {
  if (!issueDetail.value?.evidence_files) return [];
  try {
    return JSON.parse(issueDetail.value.evidence_files);
  } catch {
    return [];
  }
});

const canRespond = computed(() => {
  return issueDetail.value?.assigned_to === authStore.userInfo?.id;
});

const canVerify = computed(() => {
  // PQE 可以验证（这里简化处理，实际应该检查用户角色）
  return true;
});

const canClose = computed(() => {
  // PQE 可以关闭（这里简化处理，实际应该检查用户角色）
  return true;
});

// 获取状态标签类型
const getStatusTagType = (status?: ProcessIssueStatus): string => {
  if (!status) return 'info';
  const typeMap: Record<ProcessIssueStatus, string> = {
    open: 'warning',
    in_progress: 'primary',
    verifying: 'info',
    closed: 'success'
  };
  return typeMap[status] || 'info';
};

// 获取状态标签文本
const getStatusLabel = (status?: ProcessIssueStatus): string => {
  if (!status) return '';
  const labelMap: Record<ProcessIssueStatus, string> = {
    open: '待处理',
    in_progress: '处理中',
    verifying: '验证中',
    closed: '已关闭'
  };
  return labelMap[status] || status;
};

// 获取责任类别标签类型
const getResponsibilityTagType = (category?: ResponsibilityCategory): string => {
  if (!category) return 'info';
  const typeMap: Record<ResponsibilityCategory, string> = {
    material_defect: 'danger',
    operation_defect: 'warning',
    equipment_defect: 'info',
    process_defect: 'primary',
    design_defect: 'success'
  };
  return typeMap[category] || 'info';
};

// 获取责任类别标签文本
const getResponsibilityLabel = (category?: ResponsibilityCategory): string => {
  if (!category) return '';
  const labelMap: Record<ResponsibilityCategory, string> = {
    material_defect: '物料不良',
    operation_defect: '作业不良',
    equipment_defect: '设备不良',
    process_defect: '工艺不良',
    design_defect: '设计不良'
  };
  return labelMap[category] || category;
};

// 格式化日期时间
const formatDateTime = (dateTime?: string): string => {
  if (!dateTime) return '';
  return new Date(dateTime).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// 获取文件名
const getFileName = (path: string): string => {
  return path.split('/').pop() || path;
};

// 加载详情
const loadDetail = async () => {
  const id = Number(route.params.id);
  if (!id) return;

  loading.value = true;
  try {
    issueDetail.value = await getProcessIssue(id);
  } catch (error) {
    console.error('Failed to load issue detail:', error);
    ElMessage.error('加载问题单详情失败');
  } finally {
    loading.value = false;
  }
};

// 提交对策
const handleSubmitResponse = async () => {
  if (!responseFormRef.value || !issueDetail.value) return;

  try {
    await responseFormRef.value.validate();

    // 处理证据文件
    const evidence_files = evidenceInput.value
      ? evidenceInput.value.split(',').map(f => f.trim()).filter(f => f)
      : [];

    submitting.value = true;

    await respondToProcessIssue(issueDetail.value.id, {
      ...responseForm,
      evidence_files
    });

    ElMessage.success('对策提交成功');
    showResponseDialog.value = false;
    loadDetail();
  } catch (error) {
    if (error !== false) {
      console.error('Failed to submit response:', error);
      ElMessage.error('对策提交失败');
    }
  } finally {
    submitting.value = false;
  }
};

// 提交验证
const handleSubmitVerify = async () => {
  if (!verifyFormRef.value || !issueDetail.value) return;

  try {
    await verifyFormRef.value.validate();

    submitting.value = true;

    await verifyProcessIssue(issueDetail.value.id, verifyForm);

    ElMessage.success('验证提交成功');
    showVerifyDialog.value = false;
    loadDetail();
  } catch (error) {
    if (error !== false) {
      console.error('Failed to submit verification:', error);
      ElMessage.error('验证提交失败');
    }
  } finally {
    submitting.value = false;
  }
};

// 提交关闭
const handleSubmitClose = async () => {
  if (!issueDetail.value) return;

  submitting.value = true;
  try {
    await closeProcessIssue(issueDetail.value.id, closeForm);

    ElMessage.success('问题单已关闭');
    showCloseDialog.value = false;
    loadDetail();
  } catch (error) {
    console.error('Failed to close issue:', error);
    ElMessage.error('关闭问题单失败');
  } finally {
    submitting.value = false;
  }
};

// 返回列表
const handleBack = () => {
  router.push({ name: 'ProcessIssueList' });
};

// 生命周期
onMounted(() => {
  loadDetail();
});
</script>

<style scoped>
.process-issue-detail {
  padding: 20px;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.evidence-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.evidence-item {
  padding: 8px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.action-buttons {
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .process-issue-detail {
    padding: 12px;
  }

  .action-buttons {
    flex-direction: column;
  }

  .action-buttons .el-button {
    width: 100%;
  }
}
</style>
