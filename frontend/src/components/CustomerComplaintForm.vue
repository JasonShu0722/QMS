<template>
  <el-form
    ref="formRef"
    :model="formData"
    :rules="rules"
    label-width="120px"
    class="customer-complaint-form"
  >
    <el-form-item label="客诉类型" prop="complaint_type">
      <el-radio-group v-model="formData.complaint_type">
        <el-radio label="0km">0KM客诉</el-radio>
        <el-radio label="after_sales">售后客诉</el-radio>
      </el-radio-group>
    </el-form-item>

    <el-form-item label="客户代码" prop="customer_code">
      <el-input v-model="formData.customer_code" placeholder="请输入客户代码" />
    </el-form-item>

    <el-form-item label="产品类型" prop="product_type">
      <el-input v-model="formData.product_type" placeholder="请输入产品类型" />
    </el-form-item>

    <el-form-item label="缺陷描述" prop="defect_description">
      <el-input
        v-model="formData.defect_description"
        type="textarea"
        :rows="4"
        placeholder="请详细描述缺陷情况"
      />
    </el-form-item>

    <el-form-item label="严重度等级" prop="severity_level">
      <el-input v-model="formData.severity_level" placeholder="请输入严重度等级" />
      <div class="text-xs text-gray-500 mt-1">具体分级方案待产品定义</div>
    </el-form-item>

    <!-- 售后客诉特有字段 -->
    <template v-if="formData.complaint_type === 'after_sales'">
      <el-form-item label="VIN码" prop="vin_code">
        <el-input v-model="formData.vin_code" placeholder="请输入车辆识别码" />
      </el-form-item>

      <el-form-item label="失效里程(km)" prop="mileage">
        <el-input-number
          v-model="formData.mileage"
          :min="0"
          :controls="false"
          placeholder="请输入失效里程"
          class="w-full"
        />
      </el-form-item>

      <el-form-item label="购车日期" prop="purchase_date">
        <el-date-picker
          v-model="formData.purchase_date"
          type="date"
          placeholder="选择购车日期"
          value-format="YYYY-MM-DD"
          class="w-full"
        />
      </el-form-item>
    </template>

    <el-form-item>
      <el-button type="primary" @click="handleSubmit" :loading="submitting">
        提交
      </el-button>
      <el-button @click="handleCancel">取消</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { ElMessage, type FormInstance, type FormRules } from 'element-plus';
import { createCustomerComplaint } from '@/api/customer-quality';
import type { CustomerComplaintCreate, ComplaintType } from '@/types/customer-quality';

// 定义事件
const emit = defineEmits<{
  success: [];
  cancel: [];
}>();

// 表单引用
const formRef = ref<FormInstance>();
const submitting = ref(false);

// 表单数据
const formData = reactive<CustomerComplaintCreate>({
  complaint_type: '0km' as ComplaintType,
  customer_code: '',
  product_type: '',
  defect_description: '',
  severity_level: '',
  vin_code: undefined,
  mileage: undefined,
  purchase_date: undefined
});

// 表单验证规则
const rules: FormRules = {
  complaint_type: [
    { required: true, message: '请选择客诉类型', trigger: 'change' }
  ],
  customer_code: [
    { required: true, message: '请输入客户代码', trigger: 'blur' }
  ],
  product_type: [
    { required: true, message: '请输入产品类型', trigger: 'blur' }
  ],
  defect_description: [
    { required: true, message: '请输入缺陷描述', trigger: 'blur' },
    { min: 10, message: '缺陷描述至少10个字符', trigger: 'blur' }
  ],
  severity_level: [
    { required: true, message: '请输入严重度等级', trigger: 'blur' }
  ]
};

/**
 * 提交表单
 */
async function handleSubmit() {
  if (!formRef.value) return;

  try {
    await formRef.value.validate();
    submitting.value = true;

    await createCustomerComplaint(formData);
    ElMessage.success('客诉单创建成功');
    emit('success');
  } catch (error: any) {
    if (error !== false) { // 不是表单验证错误
      ElMessage.error(error.message || '创建客诉单失败');
      console.error('Create complaint error:', error);
    }
  } finally {
    submitting.value = false;
  }
}

/**
 * 取消
 */
function handleCancel() {
  emit('cancel');
}
</script>

<style scoped>
.customer-complaint-form {
  padding: 20px 0;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .customer-complaint-form :deep(.el-form-item__label) {
    width: 100px !important;
  }
}
</style>
