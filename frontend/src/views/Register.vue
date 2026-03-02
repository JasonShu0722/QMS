<template>
  <div class="register-container">
    <!-- 桌面端布局 (Element Plus) -->
    <div v-if="!isMobile" class="desktop-layout">
      <el-card class="register-card">
        <template #header>
          <div class="card-header">
            <h2>用户注册</h2>
            <p class="subtitle">User Registration</p>
          </div>
        </template>

        <!-- 用户类型选择 -->
        <el-radio-group v-model="userType" class="user-type-selector" size="large">
          <el-radio-button value="internal">公司员工</el-radio-button>
          <el-radio-button value="supplier">供应商</el-radio-button>
        </el-radio-group>

        <!-- 注册表单 -->
        <el-form
          ref="registerFormRef"
          :model="registerForm"
          :rules="registerRules"
          label-width="100px"
          class="register-form"
        >
          <!-- 基本信息 -->
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="registerForm.username"
              placeholder="请输入用户名（3-50个字符）"
              clearable
            />
          </el-form-item>

          <el-form-item label="姓名" prop="full_name">
            <el-input
              v-model="registerForm.full_name"
              placeholder="请输入真实姓名"
              clearable
            />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="registerForm.password"
              type="password"
              placeholder="至少8位，包含大小写字母、数字、特殊字符中至少三种"
              show-password
              clearable
            />
          </el-form-item>

          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              show-password
              clearable
            />
          </el-form-item>

          <el-form-item label="邮箱" prop="email">
            <el-input
              v-model="registerForm.email"
              placeholder="请输入邮箱地址"
              clearable
            />
          </el-form-item>

          <el-form-item label="电话" prop="phone">
            <el-input
              v-model="registerForm.phone"
              placeholder="请输入联系电话"
              clearable
            />
          </el-form-item>

          <!-- 内部员工专属字段 -->
          <template v-if="userType === 'internal'">
            <el-form-item label="部门" prop="department">
              <el-select
                v-model="registerForm.department"
                placeholder="请选择部门"
                clearable
                style="width: 100%"
              >
                <el-option label="质量部" value="质量部" />
                <el-option label="生产部" value="生产部" />
                <el-option label="技术部" value="技术部" />
                <el-option label="采购部" value="采购部" />
                <el-option label="研发部" value="研发部" />
                <el-option label="管理部" value="管理部" />
              </el-select>
            </el-form-item>

            <el-form-item label="职位" prop="position">
              <el-input
                v-model="registerForm.position"
                placeholder="请输入职位"
                clearable
              />
            </el-form-item>
          </template>

          <!-- 供应商专属字段 -->
          <template v-if="userType === 'supplier'">
            <el-form-item label="供应商" prop="supplier_id">
              <SupplierSearch
                v-model="registerForm.supplier_id"
                v-model:supplier-name="selectedSupplierName"
              />
            </el-form-item>

            <el-form-item label="职位" prop="position">
              <el-input
                v-model="registerForm.position"
                placeholder="请输入职位"
                clearable
              />
            </el-form-item>
          </template>

          <!-- 提交按钮 -->
          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              class="submit-button"
              @click="handleRegister"
            >
              提交注册
            </el-button>
            <el-button
              size="large"
              class="cancel-button"
              @click="router.push('/login')"
            >
              返回登录
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- 移动端布局 (Tailwind CSS) -->
    <div v-else class="mobile-layout">
      <div class="flex flex-col items-center justify-start min-h-screen p-4 pt-8">
        <!-- Logo 和标题 -->
        <div class="text-center mb-6">
          <h2 class="text-2xl font-bold text-white mb-1">用户注册</h2>
          <p class="text-white text-opacity-80 text-sm">User Registration</p>
        </div>

        <!-- 移动端表单卡片 -->
        <div class="w-full max-w-md bg-white rounded-lg shadow-xl p-6">
          <!-- 用户类型选择 -->
          <div class="flex gap-2 mb-6">
            <button
              :class="[
                'flex-1 py-3 rounded-lg font-medium transition-all',
                userType === 'internal'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-600'
              ]"
              @click="userType = 'internal'"
            >
              公司员工
            </button>
            <button
              :class="[
                'flex-1 py-3 rounded-lg font-medium transition-all',
                userType === 'supplier'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-100 text-gray-600'
              ]"
              @click="userType = 'supplier'"
            >
              供应商
            </button>
          </div>

          <!-- 表单 -->
          <form @submit.prevent="handleRegister">
            <!-- 用户名 -->
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-1">用户名</label>
              <input
                v-model="registerForm.username"
                type="text"
                placeholder="3-50个字符"
                class="w-full px-4 py-3 text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <!-- 姓名 -->
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-1">姓名</label>
              <input
                v-model="registerForm.full_name"
                type="text"
                placeholder="请输入真实姓名"
                class="w-full px-4 py-3 text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <!-- 密码 -->
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-1">密码</label>
              <input
                v-model="registerForm.password"
                type="password"
                placeholder="至少8位，包含大小写字母、数字等"
                class="w-full px-4 py-3 text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <!-- 确认密码 -->
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-1">确认密码</label>
              <input
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="请再次输入密码"
                class="w-full px-4 py-3 text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <!-- 邮箱 -->
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
              <input
                v-model="registerForm.email"
                type="email"
                placeholder="请输入邮箱地址"
                class="w-full px-4 py-3 text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <!-- 电话 -->
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-1">电话</label>
              <input
                v-model="registerForm.phone"
                type="tel"
                placeholder="请输入联系电话"
                class="w-full px-4 py-3 text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <!-- 内部员工字段 -->
            <template v-if="userType === 'internal'">
              <div class="mb-4">
                <label class="block text-sm font-medium text-gray-700 mb-1">部门</label>
                <select
                  v-model="registerForm.department"
                  class="w-full px-4 py-3 text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">请选择部门</option>
                  <option value="质量部">质量部</option>
                  <option value="生产部">生产部</option>
                  <option value="技术部">技术部</option>
                  <option value="采购部">采购部</option>
                  <option value="研发部">研发部</option>
                  <option value="管理部">管理部</option>
                </select>
              </div>

              <div class="mb-4">
                <label class="block text-sm font-medium text-gray-700 mb-1">职位</label>
                <input
                  v-model="registerForm.position"
                  type="text"
                  placeholder="请输入职位"
                  class="w-full px-4 py-3 text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </template>

            <!-- 供应商字段 -->
            <template v-if="userType === 'supplier'">
              <div class="mb-4">
                <label class="block text-sm font-medium text-gray-700 mb-1">供应商</label>
                <SupplierSearch
                  v-model="registerForm.supplier_id"
                  v-model:supplier-name="selectedSupplierName"
                  mobile
                />
              </div>

              <div class="mb-4">
                <label class="block text-sm font-medium text-gray-700 mb-1">职位</label>
                <input
                  v-model="registerForm.position"
                  type="text"
                  placeholder="请输入职位"
                  class="w-full px-4 py-3 text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </template>

            <!-- 提交按钮 -->
            <button
              type="submit"
              :disabled="loading"
              class="w-full py-3 text-lg font-medium text-white bg-blue-500 rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors mb-3"
            >
              {{ loading ? '提交中...' : '提交注册' }}
            </button>

            <button
              type="button"
              class="w-full py-3 text-lg font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              @click="router.push('/login')"
            >
              返回登录
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import SupplierSearch from '@/components/SupplierSearch.vue'

// 响应式状态
const router = useRouter()
const registerFormRef = ref<FormInstance>()

// 检测是否为移动端
const isMobile = ref(window.innerWidth < 768)

// 用户类型
const userType = ref<'internal' | 'supplier'>('internal')

// 注册表单
const registerForm = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  full_name: '',
  email: '',
  phone: '',
  department: '',
  position: '',
  supplier_id: undefined as number | undefined
})

// 选中的供应商名称（用于显示）
const selectedSupplierName = ref('')

// 其他状态
const loading = ref(false)

// 密码复杂度验证
const validatePassword = (_rule: any, value: any, callback: any) => {
  if (!value) {
    callback(new Error('请输入密码'))
    return
  }
  
  if (value.length < 8) {
    callback(new Error('密码长度至少8位'))
    return
  }
  
  // 检查密码复杂度：大写、小写、数字、特殊字符中至少三种
  let complexity = 0
  if (/[a-z]/.test(value)) complexity++
  if (/[A-Z]/.test(value)) complexity++
  if (/[0-9]/.test(value)) complexity++
  if (/[^a-zA-Z0-9]/.test(value)) complexity++
  
  if (complexity < 3) {
    callback(new Error('密码必须包含大写、小写、数字、特殊字符中至少三种'))
    return
  }
  
  callback()
}

// 确认密码验证
const validateConfirmPassword = (_rule: any, value: any, callback: any) => {
  if (!value) {
    callback(new Error('请再次输入密码'))
    return
  }
  
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
    return
  }
  
  callback()
}

// 表单验证规则
const registerRules = computed<FormRules>(() => ({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  password: [
    { required: true, validator: validatePassword, trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, validator: validateConfirmPassword, trigger: 'blur' }
  ],
  full_name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
    { min: 2, max: 100, message: '姓名长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号码', trigger: 'blur' }
  ],
  department: userType.value === 'internal'
    ? [{ required: true, message: '请选择部门', trigger: 'change' }]
    : [],
  supplier_id: userType.value === 'supplier'
    ? [{ required: true, message: '请选择供应商', trigger: 'change' }]
    : []
}))

// 监听窗口大小变化
const handleResize = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

// 处理注册
const handleRegister = async () => {
  // 移动端简单验证
  if (isMobile.value) {
    if (!registerForm.username || !registerForm.password || !registerForm.full_name || !registerForm.email) {
      ElMessage.error('请填写所有必填项')
      return
    }
    
    if (registerForm.password !== registerForm.confirmPassword) {
      ElMessage.error('两次输入的密码不一致')
      return
    }
    
    if (userType.value === 'internal' && !registerForm.department) {
      ElMessage.error('请选择部门')
      return
    }
    
    if (userType.value === 'supplier' && !registerForm.supplier_id) {
      ElMessage.error('请选择供应商')
      return
    }
  } else {
    // 桌面端使用 Element Plus 表单验证
    if (!registerFormRef.value) return
    
    const valid = await registerFormRef.value.validate().catch(() => false)
    if (!valid) return
  }

  loading.value = true

  try {
    // 动态导入 API
    const { authApi } = await import('@/api/auth')
    
    // 构建注册数据
    const registerData: any = {
      username: registerForm.username,
      password: registerForm.password,
      full_name: registerForm.full_name,
      email: registerForm.email,
      phone: registerForm.phone || undefined,
      user_type: userType.value,
      position: registerForm.position || undefined
    }
    
    // 根据用户类型添加特定字段
    if (userType.value === 'internal') {
      registerData.department = registerForm.department
    } else {
      registerData.supplier_id = registerForm.supplier_id
    }
    
    const response = await authApi.register(registerData)
    
    ElMessage.success(response.message || '注册成功，请等待管理员审核')
    
    // 延迟跳转到登录页
    setTimeout(() => {
      router.push('/login')
    }, 2000)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '注册失败，请检查输入信息')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 桌面端样式 */
.register-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.desktop-layout {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
}

.register-card {
  width: 100%;
  max-width: 600px;
  border-radius: 12px;
}

.card-header {
  text-align: center;
}

.card-header h2 {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

.card-header .subtitle {
  margin: 0;
  font-size: 14px;
  color: #909399;
}

.user-type-selector {
  width: 100%;
  display: flex;
  margin-bottom: 24px;
}

.user-type-selector :deep(.el-radio-button) {
  flex: 1;
}

.user-type-selector :deep(.el-radio-button__inner) {
  width: 100%;
  border-radius: 8px;
}

.register-form {
  margin-top: 24px;
}

.submit-button,
.cancel-button {
  width: 48%;
  border-radius: 8px;
  height: 44px;
  font-size: 16px;
  font-weight: 500;
}

.submit-button {
  margin-right: 4%;
}

/* 移动端样式 */
.mobile-layout {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .desktop-layout {
    display: none;
  }
}

@media (min-width: 769px) {
  .mobile-layout {
    display: none;
  }
}
</style>
