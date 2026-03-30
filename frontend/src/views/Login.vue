<template>
  <div class="login-container">
    <div v-if="!isMobile" class="desktop-layout">
      <el-card :class="['login-card', isPreviewMode ? 'login-card--preview' : '']">
        <template #header>
          <div class="card-header">
            <h2>质量管理系统</h2>
            <p class="subtitle">Quality Management System</p>
          </div>
        </template>

        <div v-if="isPreviewMode" class="preview-banner">
          ⚠️ 预览环境，仅限授权用户
        </div>

        <div class="env-switcher">
          <span :class="['env-label', !isPreviewMode ? 'env-label--active-stable' : '']">🏢 正式版</span>
          <el-switch
            :model-value="isPreviewMode"
            active-color="#e6a23c"
            inactive-color="#409eff"
            inline-prompt
            active-text=""
            inactive-text=""
            @change="handleEnvironmentToggle"
          />
          <span :class="['env-label', isPreviewMode ? 'env-label--active-preview' : '']">🧪 预览版</span>
        </div>

        <el-radio-group v-model="userType" class="user-type-selector" size="large">
          <el-radio-button value="internal">员工登录</el-radio-button>
          <el-radio-button value="supplier">供应商登录</el-radio-button>
        </el-radio-group>

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
                title="点击刷新验证码"
                @click="refreshCaptcha"
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

          <el-form-item>
            <el-checkbox v-model="rememberPassword">记住密码</el-checkbox>
          </el-form-item>

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

          <el-form-item v-if="userType === 'internal'">
            <el-button size="large" disabled class="sso-button">
              <el-icon><Connection /></el-icon>
              SSO 单点登录（即将上线）
            </el-button>
          </el-form-item>

          <div class="footer-links">
            <router-link to="/register" class="register-link">
              还没有账号？立即注册
            </router-link>
          </div>
        </el-form>
      </el-card>
    </div>

    <div v-else class="mobile-layout">
      <div class="flex flex-col items-center justify-center min-h-screen p-4">
        <div class="text-center mb-8">
          <h2 class="text-3xl font-bold text-white mb-2">质量管理系统</h2>
          <p class="text-white text-opacity-80">Quality Management System</p>
        </div>

        <div class="w-full max-w-md bg-white rounded-lg shadow-xl p-6">
          <div class="flex gap-2 mb-4">
            <div
              v-if="isPreviewMode"
              class="w-full mb-2 py-2 px-3 bg-orange-100 border border-orange-400 rounded-lg text-orange-700 text-sm text-center"
            >
              ⚠️ 预览环境，仅限授权用户
            </div>
          </div>

          <div class="flex items-center justify-center gap-3 mb-4">
            <span :class="['text-sm font-medium', !isPreviewMode ? 'text-blue-600' : 'text-gray-400']">🏢 正式版</span>
            <label class="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                :checked="isPreviewMode"
                class="sr-only peer"
                @change="handleEnvironmentToggle"
              >
              <div class="w-11 h-6 rounded-full peer-focus:outline-none peer bg-blue-500 peer-checked:bg-orange-400 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-full"></div>
            </label>
            <span :class="['text-sm font-medium', isPreviewMode ? 'text-orange-500' : 'text-gray-400']">🧪 预览版</span>
          </div>

          <div class="flex gap-2 mb-6">
            <button
              :class="[
                'flex-1 py-3 rounded-lg font-medium transition-all',
                userType === 'internal' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-600'
              ]"
              @click="userType = 'internal'"
            >
              员工登录
            </button>
            <button
              :class="[
                'flex-1 py-3 rounded-lg font-medium transition-all',
                userType === 'supplier' ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-600'
              ]"
              @click="userType = 'supplier'"
            >
              供应商登录
            </button>
          </div>

          <form @submit.prevent="handleLogin">
            <div class="mb-4">
              <input
                v-model="loginForm.username"
                type="text"
                placeholder="用户名"
                class="w-full px-4 py-3 text-lg border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div class="mb-4">
              <input
                v-model="loginForm.password"
                type="password"
                placeholder="密码"
                class="w-full px-4 py-3 text-lg border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

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

            <button
              type="submit"
              :disabled="loading"
              class="w-full py-3 text-lg font-medium text-white bg-blue-500 rounded-lg hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {{ loading ? '登录中...' : '登录' }}
            </button>

            <button
              v-if="userType === 'internal'"
              type="button"
              disabled
              class="w-full mt-3 py-3 text-lg font-medium text-gray-400 bg-gray-100 rounded-lg cursor-not-allowed"
            >
              SSO 单点登录（即将上线）
            </button>

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
import { useEnvironment } from '@/composables/useEnvironment'

const router = useRouter()
const authStore = useAuthStore()
const loginFormRef = ref<FormInstance>()
const { currentEnvironment, isPreview, switchEnvironment, syncEnvironmentState } = useEnvironment()

const isMobile = ref(window.innerWidth < 768)
const userType = ref<'internal' | 'supplier'>('internal')

const loginForm = reactive({
  username: '',
  password: '',
  captcha: ''
})

const captchaImage = ref<string>('')
const captchaId = ref<string>('')
const rememberPassword = ref(false)
const loading = ref(false)
const isPreviewMode = computed(() => isPreview.value)

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

const handleResize = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  syncEnvironmentState()

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

watch(userType, (newType) => {
  if (newType === 'supplier' && !captchaImage.value) {
    refreshCaptcha()
  }
  loginForm.captcha = ''
})

const handleEnvironmentToggle = () => {
  switchEnvironment()
}

const refreshCaptcha = async () => {
  try {
    const response = await authApi.getCaptcha()
    captchaImage.value = response.captcha_image
    captchaId.value = response.captcha_id
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '获取验证码失败')
  }
}

const handleLogin = async () => {
  if (isMobile.value) {
    if (!loginForm.username || !loginForm.password) {
      ElMessage.error('请填写用户名和密码')
      return
    }
    if (userType.value === 'supplier' && !loginForm.captcha) {
      ElMessage.error('请输入验证码')
      return
    }
  } else {
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
      userType.value === 'supplier' ? captchaId.value : undefined,
      currentEnvironment.value
    )

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
    router.push('/workbench')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '登录失败，请检查用户名和密码')

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

.env-switcher {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 10px 0 16px;
  border-bottom: 1px solid #ebedf0;
  margin-bottom: 16px;
}

.env-label {
  font-size: 14px;
  font-weight: 500;
  color: #c0c4cc;
  transition: color 0.3s;
}

.env-label--active-stable {
  color: #409eff;
  font-weight: 600;
}

.env-label--active-preview {
  color: #e6a23c;
  font-weight: 600;
}

.login-card--preview {
  border: 2px solid #e6a23c !important;
}

.login-card--preview :deep(.el-card__header) {
  background: linear-gradient(135deg, #fdf6ec, #faecd8);
}

.preview-banner {
  background: #e6a23c;
  color: #fff;
  text-align: center;
  font-size: 12px;
  font-weight: 500;
  padding: 6px 12px;
  margin: -12px -20px 16px;
  letter-spacing: 0.5px;
}

.mobile-layout {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

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
