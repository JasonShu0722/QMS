<template>
  <div class="login-container">
    <!-- 桌面端布局 (Element Plus) -->
    <div v-if="!isMobile" class="desktop-layout">
      <el-card class="login-card">
        <template #header>
          <div class="card-header">
            <h2>质量管理系统</h2>
            <p class="subtitle">Quality Management System</p>
          </div>
        </template>

        <!-- 用户类型选择 -->
        <el-radio-group v-model="userType" class="user-type-selector" size="large">
          <el-radio-button value="internal">员工登录</el-radio-button>
          <el-radio-button value="supplier">供应商登录</el-radio-button>
        </el-radio-group>

        <!-- 登录表单 -->
        <el-form
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          class="login-form"
          @keyup.enter="handleLogin"
        >
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="用户名"
              prefix-icon="User"
              size="large"
              clearable
            />
          </el-form-item>

          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="密码"
              prefix-icon="Lock"
              size="large"
              show-password
              clearable
            />
          </el-form-item>

          <!-- 供应商登录需要验证码 -->
          <el-form-item v-if="userType === 'supplier'" prop="captcha">
            <div class="captcha-row">
              <el-input
                v-model="loginForm.captcha"
                placeholder="验证码"
                prefix-icon="Picture"
                size="large"
                clearable
                style="flex: 1"
              />
              <img
                v-if="captchaImage"
                :src="captchaImage"
                alt="验证码"
                class="captcha-img"
                @click="refreshCaptcha"
                title="点击刷新验证码"
              />
              <el-button
                v-else
                type="primary"
                size="large"
                @click="refreshCaptcha"
              >
                获取验证码
              </el-button>
            </div>
          </el-form-item>

          <!-- 记住密码 -->
          <el-form-item>
            <el-checkbox v-model="rememberPassword">记住密码</el-checkbox>
          </el-form-item>

          <!-- 登录按钮 -->
          <el-form-item>
            <el-button
              type="primary"
              size="large"
              :loading="loading"
              class="login-button"
              @click="handleLogin"
            >
              登录
            </el-button>
          </el-form-item>

          <!-- SSO 登录按钮（预留，仅内部员工可见） -->
          <el-form-item v-if="userType === 'internal'">
            <el-button
              size="large"
              disabled
              class="sso-button"
            >
              <el-icon><Connection /></el-icon>
              SSO 单点登录（即将上线）
            </el-button>
          </el-form-item>

          <!-- 注册链接 -->
          <div class="footer-links">
            <router-link to="/register" class="register-link">
              还没有账号？立即注册
            </router-link>
          </div>
        </el-form>
      </el-card>
    </div>

    <!-- 移动端布局 (Tailwind CSS) -->
    <div v-else class="mobile-layout">
      <div class="flex flex-col items-center justify-center min-h-screen p-4">
        <!-- Logo 和标题 -->
        <div class="text-center mb-8">
          <h2 class="text-3xl font-bold text-white mb-2">质量管理系统</h2>
          <p class="text-white text-opacity-80">Quality Management System</p>
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
              员工登录
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
              供应商登录
            </button>
          </div>

          <!-- 表单 -->
          <form @submit.prevent="handleLogin">
            <!-- 用户名 -->
            <div class="mb-4">
              <input
                v-model="loginForm.username"
                type="text"
                placeholder="用户名"
                class="w-full px-4 py-3 text-lg border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <!-- 密码 -->
            <div class="mb-4">
              <input
                v-model="loginForm.password"
                type="password"
                placeholder="密码"
                class="w-full px-4 py-3 text-lg border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <!-- 验证码（供应商） -->
            <div v-if="userType === 'supplier'" class="mb-4">
              <div class="flex gap-2">
                <input
                  v-model="loginForm.captcha"
                  type="text"
                  placeholder="验证码"
                  class="flex-1 px-4 py-3 text-lg border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <img
                  v-if="captchaImage"
                  :src="captchaImage"
                  alt="验证码"
                  class="h-12 w-24 object-cover rounded-lg cursor-pointer border border-gray-300"
                  @click="refreshCaptcha"
                />
                <button
                  v-else
                  type="button"
                  class="px-4 py-3 bg-blue-500 text-white rounded-lg"
                  @click="refreshCaptcha"
                >
                  获取
                </button>
              </div>
            </div>

            <!-- 记住密码 -->
            <div class="mb-6">
              <label class="flex items-center">
                <input
                  v-model="rememberPassword"
                  type="checkbox"
                  class="w-5 h-5 text-blue-500 rounded"
                />
                <span class="ml-2 text-gray-700">记住密码</span>
              </label>
            </div>

            <!-- 登录按钮 -->
            <button
              type="submit"
              :disabled="loading"
              class="w-full py-3 text-lg font-medium text-white bg-blue-500 rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {{ loading ? '登录中...' : '登录' }}
            </button>

            <!-- SSO 按钮（预留） -->
            <button
              v-if="userType === 'internal'"
              type="button"
              disabled
              class="w-full mt-3 py-3 text-lg font-medium text-gray-400 bg-gray-100 rounded-lg cursor-not-allowed"
            >
              SSO 单点登录（即将上线）
            </button>

            <!-- 注册链接 -->
            <div class="mt-6 text-center">
              <router-link to="/register" class="text-blue-500 hover:text-blue-600">
                还没有账号？立即注册
              </router-link>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api/auth'

// 响应式状态
const router = useRouter()
const authStore = useAuthStore()
const loginFormRef = ref<FormInstance>()

// 检测是否为移动端
const isMobile = ref(window.innerWidth < 768)

// 用户类型
const userType = ref<'internal' | 'supplier'>('internal')

// 登录表单
const loginForm = reactive({
  username: '',
  password: '',
  captcha: ''
})

// 验证码相关
const captchaImage = ref<string>('')
const captchaId = ref<string>('')

// 其他状态
const rememberPassword = ref(false)
const loading = ref(false)

// 表单验证规则
const loginRules = computed<FormRules>(() => ({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码长度至少 8 个字符', trigger: 'blur' }
  ],
  captcha: userType.value === 'supplier'
    ? [{ required: true, message: '请输入验证码', trigger: 'blur' }]
    : []
}))

// 监听窗口大小变化
const handleResize = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  
  // 从 localStorage 恢复记住的密码
  const savedUsername = localStorage.getItem('remembered_username')
  const savedPassword = localStorage.getItem('remembered_password')
  const savedUserType = localStorage.getItem('remembered_user_type')
  
  if (savedUsername && savedPassword) {
    loginForm.username = savedUsername
    loginForm.password = savedPassword
    rememberPassword.value = true
    if (savedUserType) {
      userType.value = savedUserType as 'internal' | 'supplier'
    }
  }
})

// 监听用户类型变化，供应商登录时自动获取验证码
watch(userType, (newType) => {
  if (newType === 'supplier' && !captchaImage.value) {
    refreshCaptcha()
  }
  // 清空验证码输入
  loginForm.captcha = ''
})

// 刷新验证码
const refreshCaptcha = async () => {
  try {
    const response = await authApi.getCaptcha()
    captchaImage.value = response.captcha_image
    captchaId.value = response.captcha_id
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '获取验证码失败')
  }
}

// 处理登录
const handleLogin = async () => {
  // 移动端不使用 Element Plus 表单验证
  if (isMobile.value) {
    // 简单验证
    if (!loginForm.username || !loginForm.password) {
      ElMessage.error('请填写用户名和密码')
      return
    }
    if (userType.value === 'supplier' && !loginForm.captcha) {
      ElMessage.error('请输入验证码')
      return
    }
  } else {
    // 桌面端使用 Element Plus 表单验证
    if (!loginFormRef.value) return
    
    const valid = await loginFormRef.value.validate().catch(() => false)
    if (!valid) return
  }

  loading.value = true

  try {
    await authStore.login(
      loginForm.username,
      loginForm.password,
      userType.value,
      userType.value === 'supplier' ? loginForm.captcha : undefined,
      userType.value === 'supplier' ? captchaId.value : undefined
    )

    // 记住密码
    if (rememberPassword.value) {
      localStorage.setItem('remembered_username', loginForm.username)
      localStorage.setItem('remembered_password', loginForm.password)
      localStorage.setItem('remembered_user_type', userType.value)
    } else {
      localStorage.removeItem('remembered_username')
      localStorage.removeItem('remembered_password')
      localStorage.removeItem('remembered_user_type')
    }

    ElMessage.success('登录成功')
    
    // 跳转到工作台
    router.push('/workbench')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '登录失败，请检查用户名和密码')
    
    // 供应商登录失败后刷新验证码
    if (userType.value === 'supplier') {
      refreshCaptcha()
      loginForm.captcha = ''
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* 桌面端样式 */
.login-container {
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

.login-card {
  width: 100%;
  max-width: 450px;
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

.login-form {
  margin-top: 24px;
}

.captcha-row {
  display: flex;
  gap: 12px;
  align-items: center;
}

.captcha-img {
  height: 40px;
  width: 120px;
  object-fit: cover;
  border-radius: 4px;
  cursor: pointer;
  border: 1px solid #dcdfe6;
  transition: border-color 0.3s;
}

.captcha-img:hover {
  border-color: #409eff;
}

.login-button,
.sso-button {
  width: 100%;
  border-radius: 8px;
}

.login-button {
  height: 44px;
  font-size: 16px;
  font-weight: 500;
}

.sso-button {
  height: 44px;
  font-size: 16px;
}

.footer-links {
  text-align: center;
  margin-top: 16px;
}

.register-link {
  color: #409eff;
  text-decoration: none;
  font-size: 14px;
}

.register-link:hover {
  color: #66b1ff;
}

/* 移动端样式 */
.mobile-layout {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
