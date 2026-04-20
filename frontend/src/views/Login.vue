<template>
  <div :class="['login-container', isPreviewMode ? 'login-container--preview' : '']">
    <header :class="['login-topbar', isPreviewMode ? 'login-topbar--preview' : '']">
      <div class="brand-block">
        <span class="brand-mark">QMS</span>
        <span class="brand-caption">Quality Management System</span>
      </div>

      <div class="entry-environments" role="tablist" aria-label="环境切换">
        <button
          type="button"
          :class="['entry-environment', currentEnvironment === 'stable' ? 'entry-environment--active' : '']"
          @click="selectEnvironment('stable')"
        >
          正式环境
        </button>
        <button
          type="button"
          :class="[
            'entry-environment',
            currentEnvironment === 'preview' ? 'entry-environment--active entry-environment--preview' : ''
          ]"
          @click="selectEnvironment('preview')"
        >
          预览环境
        </button>
      </div>
    </header>

    <main :class="['login-stage', { 'login-stage--compact': isMobile, 'login-stage--preview': isPreviewMode }]">
      <section class="hero-panel">
        <div class="hero-copy">
          <p class="hero-kicker">Quality Management System</p>
          <h1>
            让质量更透明
            <br>
            让协同更高效
          </h1>
          <p class="hero-subtitle">Make quality visible across teams and keep collaboration moving.</p>
        </div>
      </section>

      <section class="login-panel">
        <div :class="['login-panel-shell', isPreviewMode ? 'login-panel-shell--preview' : 'login-panel-shell--stable']">
          <div class="login-panel-head">
            <h2>账号登录</h2>
            <span :class="['environment-badge', isPreviewMode ? 'environment-badge--preview' : '']">
              {{ isPreviewMode ? '预览环境' : '正式环境' }}
            </span>
          </div>

          <el-radio-group v-model="userType" class="user-type-selector" size="large">
            <el-radio-button value="internal">内部员工</el-radio-button>
            <el-radio-button value="supplier">供应商</el-radio-button>
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
                :prefix-icon="User"
                placeholder="用户名"
                size="large"
                clearable
              />
            </el-form-item>

            <el-form-item prop="password">
              <el-input
                v-model="loginForm.password"
                :prefix-icon="Lock"
                type="password"
                placeholder="密码"
                size="large"
                show-password
                clearable
              />
            </el-form-item>

            <el-form-item v-if="userType === 'supplier'" prop="captcha">
              <div class="captcha-row">
                <el-input
                  v-model="loginForm.captcha"
                  :prefix-icon="PictureFilled"
                  placeholder="验证码"
                  size="large"
                  clearable
                />

                <img
                  v-if="captchaImage"
                  :src="captchaImage"
                  alt="验证码"
                  class="captcha-image"
                  title="点击刷新验证码"
                  @click="refreshCaptcha"
                />
                <el-button
                  v-else
                  class="captcha-trigger"
                  type="primary"
                  plain
                  size="large"
                  @click="refreshCaptcha"
                >
                  获取验证码
                </el-button>
              </div>
            </el-form-item>

            <div class="form-meta">
              <el-checkbox v-model="rememberPassword">记住密码</el-checkbox>
              <router-link v-if="userType === 'internal'" to="/register" class="register-link">
                立即注册
              </router-link>
            </div>

            <el-button
              type="primary"
              size="large"
              :loading="loading"
              class="login-button"
              @click="handleLogin"
            >
              登录
            </el-button>

            <el-button
              v-if="userType === 'internal'"
              size="large"
              disabled
              class="sso-button"
            >
              <el-icon><Connection /></el-icon>
              SSO 单点登录
            </el-button>
          </el-form>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Connection, Lock, PictureFilled, User } from '@element-plus/icons-vue'
import { authApi } from '@/api/auth'
import { useEnvironment } from '@/composables/useEnvironment'
import { useAuthStore } from '@/stores/auth'
import { clearRememberedLogin, loadRememberedLogin, persistRememberedLogin } from '@/utils/loginRemembering'

const MOBILE_BREAKPOINT = 900

const router = useRouter()
const authStore = useAuthStore()
const loginFormRef = ref<FormInstance>()
const { currentEnvironment, isPreview, switchEnvironment, syncEnvironmentState } = useEnvironment()

const isMobile = ref(window.innerWidth < MOBILE_BREAKPOINT)
const userType = ref<'internal' | 'supplier'>('internal')
const rememberPassword = ref(false)
const loading = ref(false)
const captchaImage = ref('')
const captchaId = ref('')

const loginForm = reactive({
  username: '',
  password: '',
  captcha: ''
})

const isPreviewMode = computed(() => isPreview.value)

const loginRules = computed<FormRules>(() => ({
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为 3 到 50 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码长度至少为 8 个字符', trigger: 'blur' }
  ],
  captcha: userType.value === 'supplier'
    ? [{ required: true, message: '请输入验证码', trigger: 'blur' }]
    : []
}))

const handleResize = () => {
  isMobile.value = window.innerWidth < MOBILE_BREAKPOINT
}

const selectEnvironment = (target: 'stable' | 'preview') => {
  if (currentEnvironment.value !== target) {
    switchEnvironment()
  }
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

const validateFallback = () => {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.error('请填写用户名和密码')
    return false
  }

  if (userType.value === 'supplier' && !loginForm.captcha) {
    ElMessage.error('请输入验证码')
    return false
  }

  return true
}

const handleLogin = async () => {
  const passedFallback = validateFallback()
  if (!passedFallback) {
    return
  }

  const formValid = typeof loginFormRef.value?.validate === 'function'
    ? await loginFormRef.value.validate().catch(() => false)
    : true

  if (!formValid) {
    return
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
      persistRememberedLogin(localStorage, {
        username: loginForm.username,
        password: loginForm.password,
        userType: userType.value
      })
    } else {
      clearRememberedLogin(localStorage)
    }

    ElMessage.success('登录成功')
    if (authStore.passwordExpired) {
      ElMessage.warning('当前账号密码已过期，请登录后尽快修改密码')
    }
    router.push('/workbench')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '登录失败，请检查用户名和密码')

    if (userType.value === 'supplier') {
      await refreshCaptcha()
      loginForm.captcha = ''
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  syncEnvironmentState()

  const rememberedLogin = loadRememberedLogin(localStorage)

  if (rememberedLogin) {
    loginForm.username = rememberedLogin.username
    loginForm.password = rememberedLogin.password
    rememberPassword.value = true
    userType.value = rememberedLogin.userType
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})

watch(userType, async (newType) => {
  loginForm.captcha = ''

  if (newType === 'supplier' && !captchaImage.value) {
    await refreshCaptcha()
  }
})

defineExpose({
  loginForm,
  userType,
  rememberPassword,
  captchaId,
  loading,
  isMobile,
  refreshCaptcha,
  handleLogin
})
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(circle at 12% 18%, rgba(255, 255, 255, 0.18), transparent 22%),
    radial-gradient(circle at 84% 16%, rgba(255, 255, 255, 0.12), transparent 24%),
    linear-gradient(135deg, #0a73d1 0%, #1492ec 42%, #25abff 100%);
  overflow: hidden;
}

.login-container--preview {
  background:
    radial-gradient(circle at 14% 20%, rgba(255, 255, 255, 0.16), transparent 24%),
    radial-gradient(circle at 84% 14%, rgba(255, 255, 255, 0.1), transparent 22%),
    linear-gradient(135deg, #a76410 0%, #d7851c 42%, #f3a33b 100%);
}

.login-topbar {
  position: relative;
  z-index: 3;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 64px;
  padding: 0 clamp(28px, 4vw, 56px);
  background: linear-gradient(90deg, rgba(3, 70, 122, 0.84), rgba(11, 111, 188, 0.38));
  border-bottom: 1px solid rgba(255, 255, 255, 0.14);
  backdrop-filter: blur(14px);
}

.login-topbar--preview {
  background: linear-gradient(90deg, rgba(100, 52, 6, 0.88), rgba(184, 110, 18, 0.42));
}

.brand-block {
  display: flex;
  align-items: baseline;
  gap: 16px;
  color: #f8fbff;
}

.brand-mark {
  font-size: clamp(28px, 2.2vw, 40px);
  font-weight: 800;
  letter-spacing: 0.14em;
}

.brand-caption {
  font-size: 13px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  opacity: 0.72;
}

.entry-environments {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.entry-environment {
  min-width: 92px;
  height: 38px;
  padding: 0 16px;
  border: 1px solid rgba(255, 255, 255, 0.26);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.84);
  font-size: 14px;
  transition: all 0.24s ease;
}

.entry-environment:hover {
  border-color: rgba(255, 255, 255, 0.42);
  background: rgba(255, 255, 255, 0.14);
}

.entry-environment--active {
  background: rgba(255, 255, 255, 0.96);
  border-color: rgba(255, 255, 255, 0.96);
  color: #1377d6;
  box-shadow: 0 10px 26px rgba(7, 39, 83, 0.16);
}

.entry-environment--preview.entry-environment--active {
  color: #dd8d14;
}

.login-stage {
  position: relative;
  flex: 1;
  box-sizing: border-box;
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(360px, 420px);
  align-items: center;
  gap: clamp(24px, 3.6vw, 48px);
  min-height: 0;
  height: calc(100vh - 64px);
  padding: clamp(18px, 2.6vw, 30px) clamp(24px, 3.4vw, 52px) clamp(16px, 2.2vw, 22px);
}

.login-stage::before,
.login-stage::after,
.hero-panel::before,
.hero-panel::after {
  content: '';
  position: absolute;
  pointer-events: none;
}

.login-stage::before {
  right: 10%;
  top: 8%;
  width: 420px;
  height: 420px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.16), transparent 64%);
}

.login-stage::after {
  inset: auto auto -10% -5%;
  width: min(50vw, 760px);
  aspect-ratio: 1 / 1;
  background: repeating-linear-gradient(
    120deg,
    rgba(255, 255, 255, 0.08) 0 14px,
    rgba(255, 255, 255, 0) 14px 34px
  );
  clip-path: polygon(20% 100%, 42% 18%, 56% 18%, 88% 100%, 68% 100%, 59% 72%, 34% 72%, 27% 100%);
  opacity: 0.72;
}

.login-stage--preview::after {
  background: repeating-linear-gradient(
    120deg,
    rgba(255, 255, 255, 0.1) 0 14px,
    rgba(255, 255, 255, 0) 14px 34px
  );
}

.hero-panel {
  position: relative;
  min-height: 0;
  display: flex;
  align-items: center;
}

.hero-panel::before {
  left: 0;
  bottom: -26%;
  width: min(44vw, 640px);
  height: min(44vw, 640px);
  background: radial-gradient(circle, rgba(255, 255, 255, 0.09), transparent 66%);
}

.hero-panel::after {
  right: 6%;
  bottom: 4%;
  width: 180px;
  height: 180px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.18);
  opacity: 0.44;
}

.hero-copy {
  position: relative;
  z-index: 1;
  max-width: 620px;
  color: #ffffff;
}

.hero-kicker {
  margin: 0 0 18px;
  font-size: 15px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  opacity: 0.82;
}

.hero-copy h1 {
  margin: 0;
  font-size: clamp(36px, 4vw, 58px);
  line-height: 1.08;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.hero-subtitle {
  margin: 16px 0 0;
  font-size: clamp(17px, 1.55vw, 22px);
  line-height: 1.45;
  max-width: 500px;
  opacity: 0.88;
}

.login-panel {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: flex-end;
}

.login-panel-shell {
  --panel-title: #0f2748;
  --panel-muted: rgba(34, 59, 92, 0.74);
  --panel-field-bg: rgba(255, 255, 255, 0.96);
  --panel-field-border: rgba(15, 39, 72, 0.12);
  --panel-field-text: #223b5c;
  --panel-field-placeholder: rgba(34, 59, 92, 0.58);
  --panel-icon: rgba(34, 59, 92, 0.58);
  --panel-segment-bg: rgba(233, 242, 251, 0.96);
  --panel-segment-text: #4a6787;
  --panel-segment-border: rgba(40, 112, 184, 0.16);
  --panel-primary-start: #2d8cf0;
  --panel-primary-end: #4ba6ff;
  --panel-primary-shadow: rgba(35, 131, 228, 0.26);
  --panel-primary-contrast: #ffffff;
  --panel-secondary-bg: rgba(227, 238, 249, 0.96);
  --panel-secondary-text: #526f8d;
  --panel-secondary-border: rgba(21, 76, 136, 0.12);
  --panel-badge-bg: rgba(19, 119, 214, 0.12);
  --panel-badge-text: #1377d6;
  --panel-focus-border: rgba(47, 142, 239, 0.34);
  --panel-focus-ring: rgba(47, 142, 239, 0.1);
  --panel-trigger-border: rgba(47, 142, 239, 0.28);
  --panel-checkbox-border: rgba(47, 142, 239, 0.34);
  width: 100%;
  max-width: 420px;
  padding: 24px 24px 24px;
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(245, 250, 255, 0.92));
  box-shadow: 0 34px 72px rgba(6, 34, 73, 0.18);
  backdrop-filter: blur(16px);
}

.login-panel-shell--stable {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.97), rgba(245, 250, 255, 0.93));
}

.login-panel-shell--preview {
  --panel-title: #68370c;
  --panel-muted: rgba(104, 55, 12, 0.72);
  --panel-field-bg: rgba(255, 252, 245, 0.96);
  --panel-field-border: rgba(184, 118, 38, 0.16);
  --panel-field-text: #6d4418;
  --panel-field-placeholder: rgba(109, 68, 24, 0.54);
  --panel-icon: rgba(109, 68, 24, 0.56);
  --panel-segment-bg: rgba(255, 238, 210, 0.94);
  --panel-segment-text: #97602b;
  --panel-segment-border: rgba(202, 142, 63, 0.18);
  --panel-primary-start: #d88b22;
  --panel-primary-end: #f2a53b;
  --panel-primary-shadow: rgba(208, 130, 27, 0.24);
  --panel-primary-contrast: #fffaf0;
  --panel-secondary-bg: rgba(255, 239, 214, 0.96);
  --panel-secondary-text: #8b5a25;
  --panel-secondary-border: rgba(191, 123, 39, 0.12);
  --panel-badge-bg: rgba(221, 141, 20, 0.14);
  --panel-badge-text: #cf7f12;
  --panel-focus-border: rgba(216, 139, 34, 0.34);
  --panel-focus-ring: rgba(216, 139, 34, 0.1);
  --panel-trigger-border: rgba(216, 139, 34, 0.28);
  --panel-checkbox-border: rgba(216, 139, 34, 0.34);
  border-color: rgba(255, 212, 149, 0.92);
  background: linear-gradient(180deg, rgba(255, 248, 236, 0.98), rgba(255, 239, 214, 0.94));
  box-shadow: 0 34px 72px rgba(128, 79, 16, 0.18);
}

.login-panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.login-panel-head h2 {
  margin: 0;
  color: var(--panel-title);
  font-size: 26px;
  line-height: 1.15;
  font-weight: 700;
}

.environment-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 84px;
  height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  background: var(--panel-badge-bg);
  color: var(--panel-badge-text);
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.user-type-selector {
  width: 100%;
  display: flex;
  margin-bottom: 20px;
}

.user-type-selector :deep(.el-radio-button) {
  flex: 1;
}

.user-type-selector :deep(.el-radio-button__inner) {
  width: 100%;
  height: 44px;
  border-radius: 14px;
  border: 1px solid var(--panel-segment-border);
  background: var(--panel-segment-bg);
  color: var(--panel-segment-text);
  font-weight: 600;
  transition: all 0.24s ease;
}

.user-type-selector :deep(.el-radio-button:first-child .el-radio-button__inner) {
  border-radius: 14px;
}

.user-type-selector :deep(.el-radio-button:last-child .el-radio-button__inner) {
  border-radius: 14px;
}

.user-type-selector :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: linear-gradient(135deg, var(--panel-primary-start), var(--panel-primary-end));
  border-color: transparent;
  color: var(--panel-primary-contrast);
  box-shadow: 0 14px 28px var(--panel-primary-shadow);
}

.login-form {
  display: flex;
  flex-direction: column;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 16px;
}

.login-form :deep(.el-input__wrapper) {
  min-height: 46px;
  border-radius: 14px;
  background: var(--panel-field-bg);
  box-shadow: 0 0 0 1px var(--panel-field-border) inset;
}

.login-form :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    0 0 0 1px var(--panel-focus-border) inset,
    0 0 0 4px var(--panel-focus-ring);
}

.login-form :deep(.el-input__inner) {
  color: var(--panel-field-text);
}

.login-form :deep(.el-input__inner::placeholder) {
  color: var(--panel-field-placeholder);
}

.login-form :deep(.el-input__prefix-inner),
.login-form :deep(.el-input__suffix-inner),
.login-form :deep(.el-input__prefix-inner .el-icon),
.login-form :deep(.el-input__suffix-inner .el-icon) {
  color: var(--panel-icon);
}

.captcha-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 128px;
  gap: 12px;
  width: 100%;
}

.captcha-image,
.captcha-trigger {
  width: 128px;
  height: 46px;
  border-radius: 14px;
}

.captcha-image {
  object-fit: cover;
  cursor: pointer;
  border: 1px solid var(--panel-field-border);
  background: var(--panel-field-bg);
}

.captcha-trigger {
  border-color: var(--panel-trigger-border);
}

.form-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin: 0 0 18px;
}

.form-meta :deep(.el-checkbox__label) {
  color: var(--panel-muted);
  font-weight: 500;
}

.form-meta :deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: var(--panel-primary-start);
  border-color: var(--panel-primary-start);
}

.form-meta :deep(.el-checkbox__inner) {
  border-color: var(--panel-checkbox-border);
  background: rgba(255, 255, 255, 0.9);
}

.register-link {
  color: var(--panel-primary-start);
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
}

.register-link:hover {
  opacity: 0.88;
}

.login-button,
.sso-button {
  width: 100%;
  min-height: 46px;
  margin: 0;
  padding: 0 16px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
  box-sizing: border-box;
}

.login-button {
  margin-bottom: 12px;
  border: none;
  background: linear-gradient(135deg, var(--panel-primary-start), var(--panel-primary-end));
  box-shadow: 0 18px 30px var(--panel-primary-shadow);
}

.login-button:hover {
  opacity: 0.96;
}

.sso-button {
  background: var(--panel-secondary-bg);
  color: var(--panel-secondary-text);
  border-color: var(--panel-secondary-border);
}

.sso-button.is-disabled,
.sso-button.is-disabled:hover,
.sso-button[disabled] {
  background: var(--panel-secondary-bg);
  color: var(--panel-secondary-text);
  border-color: var(--panel-secondary-border);
  opacity: 1;
}

.sso-button :deep(.el-icon) {
  margin-right: 6px;
}

.login-form :deep(.el-button + .el-button) {
  margin-left: 0;
}

@media (max-width: 1100px) {
  .login-stage {
    grid-template-columns: minmax(0, 1fr);
    gap: 24px;
    justify-items: center;
    height: auto;
    min-height: calc(100vh - 64px);
    padding-top: 18px;
    padding-bottom: 22px;
  }

  .hero-panel {
    min-height: auto;
    width: 100%;
    justify-content: center;
    text-align: center;
  }

  .login-panel {
    width: 100%;
    justify-content: center;
  }

  .login-stage::after {
    left: 50%;
    bottom: 38%;
    width: min(70vw, 620px);
    transform: translateX(-50%);
    opacity: 0.36;
  }
}

@media (max-width: 900px) {
  .login-topbar {
    min-height: 60px;
    padding: 0 20px;
  }

  .brand-block {
    gap: 10px;
  }

  .brand-mark {
    font-size: 30px;
    letter-spacing: 0.1em;
  }

  .brand-caption {
    display: none;
  }

  .login-stage {
    min-height: calc(100vh - 60px);
    padding: 16px 20px 22px;
  }

  .login-stage--compact .hero-panel {
    padding-top: 12px;
  }

  .hero-kicker {
    margin-bottom: 14px;
    font-size: 13px;
    letter-spacing: 0.16em;
  }

  .hero-copy h1 {
    font-size: clamp(30px, 8vw, 42px);
  }

  .hero-subtitle {
    margin-top: 14px;
    font-size: 17px;
  }

  .login-panel-shell {
    padding: 20px 18px 18px;
    border-radius: 24px;
  }

  .login-panel-head {
    margin-bottom: 18px;
  }
}

@media (max-width: 640px) {
  .entry-environments {
    gap: 6px;
  }

  .entry-environment {
    min-width: 82px;
    height: 34px;
    padding: 0 12px;
    font-size: 13px;
  }

  .login-stage::after,
  .hero-panel::after {
    display: none;
  }

  .hero-copy {
    max-width: 100%;
  }

  .hero-subtitle {
    font-size: 16px;
  }

  .login-panel-shell {
    max-width: none;
  }

  .login-panel-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .captcha-row {
    grid-template-columns: minmax(0, 1fr);
  }

  .captcha-image,
  .captcha-trigger {
    width: 100%;
  }

  .form-meta {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
