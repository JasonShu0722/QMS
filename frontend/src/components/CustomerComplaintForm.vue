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

    <el-form-item label="客户名称" prop="customer_id">
      <el-select
        v-model="formData.customer_id"
        filterable
        clearable
        placeholder="请选择客户"
        class="w-full"
        :loading="customerLoading"
      >
        <el-option
          v-for="item in customerOptions"
          :key="item.id"
          :label="`${item.name} (${item.code})`"
          :value="item.id"
        />
      </el-select>
    </el-form-item>

    <el-form-item label="客户代码">
      <el-input :model-value="selectedCustomerCode" disabled placeholder="选择客户后自动带出" />
    </el-form-item>

    <el-form-item label="终端客户">
      <el-input v-model="formData.end_customer_name" placeholder="可选填写终端客户名称" />
    </el-form-item>

    <el-form-item label="产品类型" prop="product_type">
      <el-input v-model="formData.product_type" placeholder="请输入产品类型" />
    </el-form-item>

    <el-form-item label="缺陷描述" prop="defect_description">
      <el-input
        v-model="formData.defect_description"
        type="textarea"
        :rows="4"
        placeholder="请详细描述问题现象"
      />
    </el-form-item>

    <el-form-item label="涉及退件">
      <el-switch v-model="formData.is_return_required" />
    </el-form-item>

    <el-form-item label="实物解析">
      <el-switch v-model="formData.requires_physical_analysis" />
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
import {
  createCustomerComplaint,
  getCustomerComplaintCustomerOptions,
} from '@/api/customer-quality'
import { useProblemManagementStore } from '@/stores/problemManagement'
import type { CustomerComplaintCreate, CustomerComplaintCustomerOption } from '@/types/customer-quality'
import { ComplaintType } from '@/types/customer-quality'
import { buildCustomerComplaintTypeOptions } from '@/utils/problemManagement'

const emit = defineEmits<{
  success: []
  cancel: []
}>()

const formRef = ref<FormInstance>()
const submitting = ref(false)
const customerLoading = ref(false)
const customerOptions = ref<CustomerComplaintCustomerOption[]>([])
const problemManagementStore = useProblemManagementStore()

const formData = reactive<CustomerComplaintCreate>({
  complaint_type: ComplaintType.ZERO_KM,
  customer_id: undefined,
  end_customer_name: '',
  product_type: '',
  defect_description: '',
  is_return_required: false,
  requires_physical_analysis: false,
  vin_code: undefined,
  mileage: undefined,
  purchase_date: undefined,
})

const complaintTypeOptions = computed(() =>
  buildCustomerComplaintTypeOptions(problemManagementStore.getCategory)
)

const selectedCustomerCode = computed(() => {
  const selectedCustomer = customerOptions.value.find((item) => item.id === formData.customer_id)
  return selectedCustomer?.code ?? ''
})

const rules: FormRules = {
  complaint_type: [{ required: true, message: '请选择客诉类型', trigger: 'change' }],
  customer_id: [{ required: true, message: '请选择客户', trigger: 'change' }],
  product_type: [{ required: true, message: '请输入产品类型', trigger: 'blur' }],
  defect_description: [
    { required: true, message: '请输入缺陷描述', trigger: 'blur' },
    { min: 10, message: '缺陷描述至少 10 个字', trigger: 'blur' },
  ],
}

async function loadCustomerOptions() {
  customerLoading.value = true

  try {
    customerOptions.value = await getCustomerComplaintCustomerOptions()
  } catch (error: any) {
    ElMessage.error(error.message || '加载客户清单失败')
  } finally {
    customerLoading.value = false
  }
}

async function handleSubmit() {
  if (!formRef.value) {
    return
  }

  try {
    await formRef.value.validate()
    submitting.value = true

    await createCustomerComplaint({
      ...formData,
      end_customer_name: formData.end_customer_name?.trim() || undefined,
    })
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
  void loadCustomerOptions()
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
