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
        <el-radio
          v-for="option in complaintTypeOptions"
          :key="option.value"
          :label="option.value"
        >
          {{ option.label }}
        </el-radio>
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
      <div class="mt-1 text-xs text-gray-500">具体分级方案待产品定义</div>
    </el-form-item>

    <template v-if="formData.complaint_type === ComplaintType.AFTER_SALES">
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
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        提交
      </el-button>
      <el-button @click="handleCancel">取消</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { createCustomerComplaint } from '@/api/customer-quality'
import { useProblemManagementStore } from '@/stores/problemManagement'
import { ComplaintType, type CustomerComplaintCreate } from '@/types/customer-quality'
import { buildCustomerComplaintTypeOptions } from '@/utils/problemManagement'

const emit = defineEmits<{
  success: []
  cancel: []
}>()

const formRef = ref<FormInstance>()
const submitting = ref(false)
const problemManagementStore = useProblemManagementStore()

const formData = reactive<CustomerComplaintCreate>({
  complaint_type: ComplaintType.ZERO_KM,
  customer_code: '',
  product_type: '',
  defect_description: '',
  severity_level: '',
  vin_code: undefined,
  mileage: undefined,
  purchase_date: undefined
})

const complaintTypeOptions = computed(() =>
  buildCustomerComplaintTypeOptions(problemManagementStore.getCategory)
)

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
}

async function handleSubmit() {
  if (!formRef.value) {
    return
  }

  try {
    await formRef.value.validate()
    submitting.value = true

    await createCustomerComplaint(formData)
    ElMessage.success('客诉单创建成功')
    emit('success')
  } catch (error: any) {
    if (error !== false) {
      ElMessage.error(error.message || '创建客诉单失败')
      console.error('Create complaint error:', error)
    }
  } finally {
    submitting.value = false
  }
}

function handleCancel() {
  emit('cancel')
}

onMounted(() => {
  void problemManagementStore.loadCatalog()
})
</script>

<style scoped>
.customer-complaint-form {
  padding: 20px 0;
}

@media (max-width: 768px) {
  .customer-complaint-form :deep(.el-form-item__label) {
    width: 100px !important;
  }
}
</style>
