<template>
  <div class="eight-d-customer-form p-4 md:p-6">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">客诉 8D 报告</h1>
      <el-button @click="handleBack">返回</el-button>
    </div>

    <!-- 客诉单基本信息 -->
    <el-card class="mb-4" v-if="complaint">
      <template #header>
        <span class="font-semibold">客诉单信息</span>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="客诉编号">{{ complaint.complaint_number }}</el-descriptions-item>
        <el-descriptions-item label="客诉类型">
          <el-tag :type="complaint.complaint_type === '0km' ? 'danger' : 'warning'">
            {{ complaint.complaint_type === '0km' ? '0KM' : '售后' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="客户代码">{{ complaint.customer_code }}</el-descriptions-item>
        <el-descriptions-item label="产品类型">{{ complaint.product_type }}</el-descriptions-item>
        <el-descriptions-item label="缺陷描述" :span="2">{{ complaint.defect_description }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- 8D 报告内容 -->
    <el-card v-loading="loading">
      <el-tabs v-model="activeTab" type="border-card">
        <!-- D0-D3 (CQE完成) -->
        <el-tab-pane label="D0-D3 (CQE)" name="d0-d3" :disabled="!eightDData">
          <div v-if="eightDData?.d0_d3_cqe" class="space-y-4">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="问题描述 (5W2H)">
                {{ eightDData.d0_d3_cqe.problem_description }}
              </el-descriptions-item>
              <el-descriptions-item label="围堵措施">
                {{ eightDData.d0_d3_cqe.containment_actions }}
              </el-descriptions-item>
              <el-descriptions-item label="围堵范围">
                <el-tag v-if="eightDData.d0_d3_cqe.containment_in_transit" type="success" class="mr-2">在途品</el-tag>
                <el-tag v-if="eightDData.d0_d3_cqe.containment_inventory" type="success" class="mr-2">库存品</el-tag>
                <el-tag v-if="eightDData.d0_d3_cqe.containment_customer" type="success">客户端库存</el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </div>
          <el-empty v-else description="CQE 尚未完成 D0-D3 阶段" />
        </el-tab-pane>

        <!-- D4-D7 (责任板块) -->
        <el-tab-pane label="D4-D7 (责任板块)" name="d4-d7">
          <el-form
            v-if="canEditD4D7"
            ref="d4d7FormRef"
            :model="d4d7Form"
            :rules="d4d7Rules"
            label-width="140px"
          >
            <el-form-item label="根本原因" prop="root_cause">
              <el-input
                v-model="d4d7Form.root_cause"
                type="textarea"
                :rows="4"
                placeholder="请详细描述根本原因"
              />
            </el-form-item>

            <el-form-item label="分析方法" prop="analysis_method">
              <el-select v-model="d4d7Form.analysis_method" placeholder="请选择分析方法">
                <el-option label="5Why分析" value="5Why" />
                <el-option label="鱼骨图" value="鱼骨图" />
                <el-option label="FTA故障树" value="FTA" />
                <el-option label="流程分析" value="流程分析" />
              </el-select>
            </el-form-item>

            <el-form-item label="纠正措施" prop="corrective_actions">
              <el-input
                v-model="d4d7Form.corrective_actions"
                type="textarea"
                :rows="4"
                placeholder="请详细描述纠正措施"
              />
            </el-form-item>

            <el-form-item label="D6验证报告" prop="verification_report_url">
              <el-input v-model="d4d7Form.verification_report_url" placeholder="请上传验证报告附件URL">
                <template #append>
                  <el-button>上传</el-button>
                </template>
              </el-input>
              <div class="text-xs text-gray-500 mt-1">必须上传验证报告或测试数据</div>
            </el-form-item>

            <el-form-item label="是否涉及文件修改" prop="standardization">
              <el-switch v-model="d4d7Form.standardization" />
            </el-form-item>

            <el-form-item v-if="d4d7Form.standardization" label="标准化文件" prop="standardization_files">
              <el-input
                v-model="standardizationFilesInput"
                placeholder="请上传修改后的文件（多个文件用逗号分隔）"
              >
                <template #append>
                  <el-button>上传</el-button>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="handleSubmitD4D7" :loading="submitting">
                提交 D4-D7
              </el-button>
            </el-form-item>
          </el-form>

          <!-- 查看模式 -->
          <div v-else-if="eightDData?.d4_d7_responsible" class="space-y-4">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="根本原因">
                {{ eightDData.d4_d7_responsible.root_cause }}
              </el-descriptions-item>
              <el-descriptions-item label="分析方法">
                {{ eightDData.d4_d7_responsible.analysis_method }}
              </el-descriptions-item>
              <el-descriptions-item label="纠正措施">
                {{ eightDData.d4_d7_responsible.corrective_actions }}
              </el-descriptions-item>
              <el-descriptions-item label="验证报告">
                <a v-if="eightDData.d4_d7_responsible.verification_report_url" 
                   :href="eightDData.d4_d7_responsible.verification_report_url" 
                   target="_blank"
                   class="text-blue-500 hover:underline">
                  查看附件
                </a>
                <span v-else class="text-gray-400">未上传</span>
              </el-descriptions-item>
              <el-descriptions-item label="标准化">
                <el-tag :type="eightDData.d4_d7_responsible.standardization ? 'success' : 'info'">
                  {{ eightDData.d4_d7_responsible.standardization ? '已修改文件' : '无需修改' }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </div>

          <el-empty v-else description="责任板块尚未填写 D4-D7" />
        </el-tab-pane>

        <!-- D8 (水平展开) -->
        <el-tab-pane label="D8 (水平展开)" name="d8">
          <el-form
            v-if="canEditD8"
            ref="d8FormRef"
            :model="d8Form"
            :rules="d8Rules"
            label-width="140px"
          >
            <el-form-item label="水平展开项目" prop="horizontal_deployment">
              <el-select
                v-model="d8Form.horizontal_deployment"
                multiple
                filterable
                allow-create
                placeholder="搜索或输入类似产品/工艺"
                class="w-full"
              >
                <el-option label="类似产品A" value="类似产品A" />
                <el-option label="类似产品B" value="类似产品B" />
                <el-option label="类似工艺C" value="类似工艺C" />
              </el-select>
              <div class="text-xs text-gray-500 mt-1">将对策推送到相关项目组</div>
            </el-form-item>

            <el-form-item label="经验教训" prop="lessons_learned">
              <el-input
                v-model="d8Form.lessons_learned"
                type="textarea"
                :rows="4"
                placeholder="请总结经验教训"
              />
            </el-form-item>

            <el-form-item label="沉淀到经验库" prop="save_to_library">
              <el-switch v-model="d8Form.save_to_library" />
              <div class="text-xs text-gray-500 mt-1">勾选后将自动保存到经验教训库</div>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="handleSubmitD8" :loading="submitting">
                提交 D8
              </el-button>
            </el-form-item>
          </el-form>

          <!-- 查看模式 -->
          <div v-else-if="eightDData?.d8_horizontal" class="space-y-4">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="水平展开项目">
                <el-tag
                  v-for="item in eightDData.d8_horizontal.horizontal_deployment"
                  :key="item"
                  class="mr-2"
                >
                  {{ item }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="经验教训">
                {{ eightDData.d8_horizontal.lessons_learned }}
              </el-descriptions-item>
              <el-descriptions-item label="经验库">
                <el-tag :type="eightDData.d8_horizontal.save_to_library ? 'success' : 'info'">
                  {{ eightDData.d8_horizontal.save_to_library ? '已沉淀' : '未沉淀' }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </div>

          <el-empty v-else description="尚未完成 D8 阶段" />
        </el-tab-pane>

        <!-- 审核 -->
        <el-tab-pane label="审核" name="review" v-if="canReview">
          <el-form
            ref="reviewFormRef"
            :model="reviewForm"
            :rules="reviewRules"
            label-width="140px"
          >
            <el-form-item label="审核结果" prop="approved">
              <el-radio-group v-model="reviewForm.approved">
                <el-radio :label="true">批准</el-radio>
                <el-radio :label="false">驳回</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="审核意见" prop="review_comments">
              <el-input
                v-model="reviewForm.review_comments"
                type="textarea"
                :rows="4"
                placeholder="请填写审核意见"
              />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="handleReview" :loading="submitting">
                提交审核
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import {
  getCustomerComplaint,
  getEightDCustomer,
  submitEightDCustomer,
  submitEightDD8,
  reviewEightDCustomer
} from '@/api/customer-quality';
import type {
  CustomerComplaint,
  EightDCustomer,
  D4D7Data,
  D8Data,
  EightDReview
} from '@/types/customer-quality';

const route = useRoute();
const router = useRouter();

// 数据状态
const loading = ref(false);
const submitting = ref(false);
const complaint = ref<CustomerComplaint | null>(null);
const eightDData = ref<EightDCustomer | null>(null);
const activeTab = ref('d0-d3');

// 表单引用
const d4d7FormRef = ref<FormInstance>();
const d8FormRef = ref<FormInstance>();
const reviewFormRef = ref<FormInstance>();

// D4-D7 表单
const d4d7Form = reactive<D4D7Data>({
  root_cause: '',
  analysis_method: '',
  corrective_actions: '',
  verification_report_url: '',
  standardization: false,
  standardization_files: []
});

const standardizationFilesInput = ref('');

// D8 表单
const d8Form = reactive<D8Data>({
  horizontal_deployment: [],
  lessons_learned: '',
  save_to_library: false
});

// 审核表单
const reviewForm = reactive<EightDReview>({
  approved: true,
  review_comments: ''
});

// 表单验证规则
const d4d7Rules: FormRules = {
  root_cause: [{ required: true, message: '请输入根本原因', trigger: 'blur' }],
  analysis_method: [{ required: true, message: '请选择分析方法', trigger: 'change' }],
  corrective_actions: [{ required: true, message: '请输入纠正措施', trigger: 'blur' }],
  verification_report_url: [{ required: true, message: '请上传验证报告', trigger: 'blur' }]
};

const d8Rules: FormRules = {
  horizontal_deployment: [{ required: true, message: '请选择水平展开项目', trigger: 'change' }],
  lessons_learned: [{ required: true, message: '请输入经验教训', trigger: 'blur' }]
};

const reviewRules: FormRules = {
  review_comments: [{ required: true, message: '请填写审核意见', trigger: 'blur' }]
};

// 权限判断
const canEditD4D7 = computed(() => {
  // TODO: 根据用户角色和8D状态判断是否可编辑
  return eightDData.value?.status === 'd4_d7_pending';
});

const canEditD8 = computed(() => {
  return eightDData.value?.status === 'd8_pending';
});

const canReview = computed(() => {
  // TODO: 根据用户角色判断是否可审核
  return eightDData.value?.status === 'under_review';
});

/**
 * 加载数据
 */
async function loadData() {
  const complaintId = Number(route.params.id);
  loading.value = true;

  try {
    // 加载客诉单信息
    complaint.value = await getCustomerComplaint(complaintId);

    // 加载8D报告
    try {
      eightDData.value = await getEightDCustomer(complaintId);
    } catch (error: any) {
      if (error.response?.status !== 404) {
        throw error;
      }
      // 8D报告不存在，这是正常情况
    }
  } catch (error) {
    ElMessage.error('加载数据失败');
    console.error('Load data error:', error);
  } finally {
    loading.value = false;
  }
}

/**
 * 提交 D4-D7
 */
async function handleSubmitD4D7() {
  if (!d4d7FormRef.value) return;

  try {
    await d4d7FormRef.value.validate();
    submitting.value = true;

    // 处理标准化文件
    if (d4d7Form.standardization && standardizationFilesInput.value) {
      d4d7Form.standardization_files = standardizationFilesInput.value.split(',').map(s => s.trim());
    }

    const complaintId = Number(route.params.id);
    await submitEightDCustomer(complaintId, { d4_d7_data: d4d7Form });

    ElMessage.success('D4-D7 提交成功');
    await loadData();
  } catch (error: any) {
    if (error !== false) {
      ElMessage.error(error.message || 'D4-D7 提交失败');
      console.error('Submit D4-D7 error:', error);
    }
  } finally {
    submitting.value = false;
  }
}

/**
 * 提交 D8
 */
async function handleSubmitD8() {
  if (!d8FormRef.value) return;

  try {
    await d8FormRef.value.validate();
    submitting.value = true;

    const complaintId = Number(route.params.id);
    await submitEightDD8(complaintId, { d8_data: d8Form });

    ElMessage.success('D8 提交成功');
    await loadData();
  } catch (error: any) {
    if (error !== false) {
      ElMessage.error(error.message || 'D8 提交失败');
      console.error('Submit D8 error:', error);
    }
  } finally {
    submitting.value = false;
  }
}

/**
 * 提交审核
 */
async function handleReview() {
  if (!reviewFormRef.value) return;

  try {
    await reviewFormRef.value.validate();
    submitting.value = true;

    const complaintId = Number(route.params.id);
    await reviewEightDCustomer(complaintId, reviewForm);

    ElMessage.success('审核提交成功');
    await loadData();
  } catch (error: any) {
    if (error !== false) {
      ElMessage.error(error.message || '审核提交失败');
      console.error('Review error:', error);
    }
  } finally {
    submitting.value = false;
  }
}

/**
 * 返回
 */
function handleBack() {
  router.back();
}

// 初始化
onMounted(() => {
  loadData();
});
</script>

<style scoped>
.eight-d-customer-form {
  min-height: 100vh;
}

/* 移动端适配 */
@media (max-width: 768px) {
  :deep(.el-form-item__label) {
    width: 100px !important;
  }

  :deep(.el-descriptions) {
    font-size: 12px;
  }
}
</style>
