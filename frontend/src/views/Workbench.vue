<template>
  <div class="workbench-container">
    <AnnouncementDialog
      v-if="featureBlocks.announcements"
      v-model="showAnnouncementDialog"
      :announcements="unreadImportantAnnouncements"
      @all-read="handleAllAnnouncementsRead"
    />

    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="6" animated />
    </div>

    <template v-else>
      <el-card class="profile-card" shadow="hover">
        <div class="profile-header">
          <div class="avatar-wrapper">
            <el-avatar :size="72" :src="avatarUrl">
              <el-icon><User /></el-icon>
            </el-avatar>
          </div>

          <input
            ref="avatarInputRef"
            type="file"
            accept="image/png,image/jpeg,image/jpg,image/webp"
            style="display: none"
            @change="handleAvatarFileChange"
          />

          <div class="profile-info">
            <div class="flex items-center gap-2">
              <h2>{{ sessionUser?.full_name || authStore.userInfo?.full_name }}</h2>
              <el-tag :type="environment === 'stable' ? 'primary' : 'warning'" size="small">
                {{ environment === 'stable' ? '正式环境' : '预览环境' }}
              </el-tag>
              <el-tag v-if="authStore.isPlatformAdmin" type="danger" size="small">平台管理员</el-tag>
            </div>
            <p class="profile-meta">
              {{ profileDescription }}
            </p>
          </div>

          <div class="profile-actions">
            <el-button class="profile-main-button" type="primary" @click="openSettingsDialog()">
              <el-icon><Setting /></el-icon>
              系统设置
            </el-button>
          </div>
        </div>
      </el-card>

      <el-row :gutter="20" class="dashboard-row">
        <el-col :xs="24" :lg="featureBlocks.metrics && authStore.isInternal ? 14 : 24">
          <el-card class="dashboard-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="card-header-title">快捷入口</span>
                <el-button link type="primary" @click="openQuickActionDialog">
                  <el-icon><Setting /></el-icon>
                  配置快捷入口
                </el-button>
              </div>
            </template>

            <div v-if="quickActions.length" class="quick-action-grid">
              <el-card
                v-for="action in quickActions"
                :key="action.link"
                class="quick-action-card"
                shadow="never"
                @click="router.push(action.link)"
              >
                <div class="quick-action-title">{{ action.title }}</div>
              </el-card>
            </div>
            <el-empty v-else description="暂无快捷入口" :image-size="90" />
          </el-card>
        </el-col>

        <el-col v-if="featureBlocks.metrics && authStore.isInternal" :xs="24" :lg="10">
          <el-card class="dashboard-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="card-header-title">指标监控</span>
              </div>
            </template>

            <div v-if="internalDashboard?.metrics?.length" class="metrics-list">
              <div v-for="metric in internalDashboard.metrics" :key="metric.key" class="metric-item">
                <div class="metric-top">
                  <span>{{ metric.name }}</span>
                  <strong :class="`metric-value metric-value--${metric.status}`">
                    {{ metric.value }}{{ metric.unit || '' }}
                  </strong>
                </div>
                <el-progress
                  v-if="metric.achievement !== undefined"
                  :percentage="metric.achievement"
                  :status="metric.status === 'good' ? 'success' : metric.status === 'warning' ? 'warning' : 'exception'"
                />
              </div>
            </div>
            <el-empty v-else description="当前没有指标数据" :image-size="90" />
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" class="dashboard-row">
        <el-col :xs="24" :md="12">
          <el-card class="dashboard-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="card-header-title">{{ taskSectionTitle }}</span>
                <el-badge :value="taskList.length" />
              </div>
            </template>

            <div v-if="taskList.length" class="todo-grid">
              <TaskCard v-for="task in taskList" :key="`${task.task_type}-${task.task_id}`" :task="task" @click="handleTaskClick" />
            </div>
            <el-empty v-else :description="taskEmptyDescription" :image-size="80" />
          </el-card>
        </el-col>

        <el-col :xs="24" :md="12">
          <el-card class="dashboard-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="card-header-title">
                  <el-icon><Bell /></el-icon>
                  {{ secondaryPanelTitle }}
                </span>
              </div>
            </template>

            <template v-if="featureBlocks.announcements">
              <AnnouncementList />
            </template>
            <template v-else>
              <div class="announcement-placeholder">
                <el-empty description="暂无公告" :image-size="88" />
              </div>
            </template>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <el-dialog
      v-model="showQuickActionDialog"
      title="配置快捷入口"
      width="880px"
      :close-on-click-modal="false"
    >
      <div class="quick-action-config-panel">
        <div class="quick-action-config-toolbar">
          <el-input
            v-model="quickActionKeyword"
            placeholder="搜索功能名称或描述"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <div class="quick-action-config-summary">
            已选择 {{ quickActionDraft.length }} 项
          </div>
        </div>

        <div class="quick-action-group-list">
          <section
            v-for="group in quickActionGroups"
            :key="group.category"
            class="quick-action-group"
          >
            <header class="quick-action-group__header">
              <h4>{{ group.category }}</h4>
              <span>{{ group.items.length }} 项</span>
            </header>

            <div class="quick-action-group__grid">
              <button
                v-for="option in group.items"
                :key="option.id"
                type="button"
                class="quick-action-option"
                :class="{ 'quick-action-option--selected': isQuickActionSelected(option.id) }"
                @click="toggleQuickAction(option.id)"
              >
                <div class="quick-action-option__check">
                  <el-icon v-if="isQuickActionSelected(option.id)"><Check /></el-icon>
                </div>
                <div class="quick-action-option__content">
                  <div class="quick-action-option__top">
                    <span class="quick-action-option__title">{{ option.title }}</span>
                    <el-tag
                      v-if="!isQuickActionAvailable(option)"
                      size="small"
                      type="warning"
                      effect="plain"
                    >
                      当前未启用
                    </el-tag>
                  </div>
                </div>
              </button>
            </div>
          </section>
        </div>

        <el-empty
          v-if="!quickActionGroups.length"
          description="没有匹配的功能项"
          :image-size="80"
        />
      </div>
      <template #footer>
        <el-button @click="resetQuickActionsToDefault">恢复默认</el-button>
        <el-button @click="showQuickActionDialog = false">取消</el-button>
        <el-button type="primary" @click="saveQuickActions">保存配置</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showSettingsDialog"
      title="系统设置"
      width="920px"
      :close-on-click-modal="false"
      class="system-settings-dialog"
    >
      <el-tabs v-model="activeSettingsTab" class="settings-tabs">
        <el-tab-pane label="账户信息" name="profile">
          <div class="settings-pane">
            <div v-if="!canEditOwnProfile" class="settings-inline-note">
              仅平台管理员可修改，请在用户管理中调整。
            </div>

            <el-form
              ref="profileFormRef"
              :model="profileForm"
              :rules="profileRules"
              label-width="96px"
              class="profile-settings-form"
            >
              <el-form-item label="用户名">
                <el-input :model-value="sessionUser?.username || ''" disabled />
              </el-form-item>
              <el-form-item label="姓名" prop="full_name">
                <el-input v-model="profileForm.full_name" :disabled="!canEditOwnProfile" placeholder="请输入姓名" />
              </el-form-item>
              <el-form-item label="邮箱" prop="email">
                <el-input v-model="profileForm.email" :disabled="!canEditOwnProfile" placeholder="请输入常用邮箱" />
              </el-form-item>
              <el-form-item label="电话" prop="phone">
                <el-input v-model="profileForm.phone" :disabled="!canEditOwnProfile" placeholder="请输入联系电话" />
              </el-form-item>
              <el-form-item v-if="authStore.isInternal" label="部门" prop="department">
                <el-input v-model="profileForm.department" :disabled="!canEditOwnProfile" placeholder="请输入部门" />
              </el-form-item>
              <el-form-item v-if="authStore.isSupplier" label="供应商">
                <el-input :model-value="sessionUser?.supplier_name || '未关联'" disabled />
              </el-form-item>
              <el-form-item label="职位" prop="position">
                <el-input v-model="profileForm.position" :disabled="!canEditOwnProfile" placeholder="请输入职位" />
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <el-tab-pane label="头像设置" name="avatar">
          <div class="settings-pane">
            <div class="avatar-settings-panel">
              <div class="avatar-settings-preview">
                <el-avatar :size="108" :src="avatarUrl">
                  <el-icon><User /></el-icon>
                </el-avatar>
                <div class="avatar-settings-preview__text">
                  <strong>{{ sessionUser?.full_name || authStore.userInfo?.full_name }}</strong>
                  <span>{{ sessionUser?.username }}</span>
                </div>
              </div>

              <div class="avatar-settings-actions">
                <el-button type="primary" @click="triggerAvatarUpload">
                  <el-icon><UploadFilled /></el-icon>
                  选择头像图片
                </el-button>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="修改密码" name="password">
          <div class="settings-pane">
            <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-width="100px">
              <el-form-item label="旧密码" prop="old_password">
                <el-input v-model="passwordForm.old_password" type="password" show-password placeholder="请输入旧密码" />
              </el-form-item>
              <el-form-item label="新密码" prop="new_password">
                <el-input v-model="passwordForm.new_password" type="password" show-password placeholder="请输入新密码" />
                <div class="password-hint">至少 8 位，包含三类字符</div>
              </el-form-item>
              <el-form-item label="确认密码" prop="confirm_password">
                <el-input v-model="passwordForm.confirm_password" type="password" show-password placeholder="请再次输入新密码" />
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <el-tab-pane label="电子签名" name="signature">
          <div class="settings-pane">
            <div class="signature-upload">
              <div v-if="currentSignature" class="current-signature">
                <h4>当前签名</h4>
                <img :src="currentSignature" alt="电子签名" class="signature-preview" />
              </div>
              <div v-else class="signature-empty">
                <el-empty description="未配置签名" :image-size="72" />
              </div>

              <el-upload
                ref="uploadRef"
                class="signature-uploader"
                drag
                :auto-upload="false"
                :limit="1"
                accept="image/png,image/jpeg,image/jpg"
                :on-change="handleSignatureChange"
                :on-exceed="handleExceed"
              >
                <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                <div class="el-upload__text">拖拽文件到此处或 <em>点击上传</em></div>
                <template #tip>
                  <div class="el-upload__tip">支持 PNG / JPG，系统会自动处理签名图片背景。</div>
                </template>
              </el-upload>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <div class="settings-dialog-footer">
          <el-button class="settings-dialog-footer__button" @click="showSettingsDialog = false">关闭</el-button>
          <el-button
            class="settings-dialog-footer__button"
            type="primary"
            :loading="settingsPrimaryLoading"
            :disabled="settingsPrimaryDisabled"
            @click="handleSettingsPrimaryAction"
          >
            {{ settingsPrimaryLabel }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showCropperDialog"
      title="裁剪头像"
      width="500px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <div class="cropper-container">
        <VueCropper
          ref="cropperRef"
          :img="cropperOption.img"
          :output-size="cropperOption.outputSize"
          :output-type="cropperOption.outputType"
          :info="false"
          :can-scale="true"
          :auto-crop="true"
          :auto-crop-width="200"
          :auto-crop-height="200"
          :fixed="true"
          :fixed-number="[1, 1]"
          :full="false"
          :fixed-box="false"
          :can-move="true"
          :can-move-box="true"
          :original="false"
          :center-box="true"
          :high="true"
          mode="contain"
        />
      </div>
      <template #footer>
        <el-button @click="showCropperDialog = false">取消</el-button>
        <el-button type="primary" :loading="avatarLoading" @click="handleCropAndUpload">确认上传</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ElMessage,
  type FormInstance,
  type FormRules,
  type UploadFile,
  type UploadInstance
} from 'element-plus'
import { Bell, Check, Search, Setting, UploadFilled, User } from '@element-plus/icons-vue'
import { VueCropper } from 'vue-cropper'
import 'vue-cropper/dist/index.css'
import { announcementApi } from '@/api/announcement'
import { workbenchApi } from '@/api/workbench'
import AnnouncementDialog from '@/components/AnnouncementDialog.vue'
import AnnouncementList from '@/components/AnnouncementList.vue'
import TaskCard from '@/components/TaskCard.vue'
import { useAuthStore } from '@/stores/auth'
import { useFeatureFlagStore } from '@/stores/featureFlag'
import {
  getConfigurableQuickActions,
  getDefaultQuickActionIds,
  getVisibleQuickActions,
  getWorkbenchQuickActionStorageKey,
  isQuickActionCurrentlyAvailable,
  sanitizeQuickActionIds,
  type WorkbenchQuickActionContext,
  type WorkbenchQuickActionOption
} from '@/config/workbenchQuickActions'
import type { Announcement } from '@/types/announcement'
import type {
  ChangePasswordRequest,
  DashboardData,
  InternalDashboard,
  ProfileUpdateRequest,
  SupplierDashboard,
  TodoTask
} from '@/types/workbench'

interface ProfileFormState {
  full_name: string
  email: string
  phone: string
  department: string
  position: string
}

type SettingsTabName = 'profile' | 'avatar' | 'password' | 'signature'

const router = useRouter()
const authStore = useAuthStore()
const featureFlagStore = useFeatureFlagStore()

const loading = ref(false)
const dashboardData = ref<DashboardData | null>(null)
const showQuickActionDialog = ref(false)
const quickActionDraft = ref<string[]>([])
const selectedQuickActionIds = ref<string[]>([])
const quickActionKeyword = ref('')

const showAnnouncementDialog = ref(false)
const unreadImportantAnnouncements = ref<Announcement[]>([])

const avatarInputRef = ref<HTMLInputElement>()
const cropperRef = ref<any>()
const showSettingsDialog = ref(false)
const activeSettingsTab = ref<SettingsTabName>('profile')
const showCropperDialog = ref(false)
const avatarLoading = ref(false)
const profileLoading = ref(false)
const profileFormRef = ref<FormInstance>()
const profileForm = reactive<ProfileFormState>({
  full_name: '',
  email: '',
  phone: '',
  department: '',
  position: ''
})
const cropperOption = reactive({
  img: '',
  outputSize: 1,
  outputType: 'png'
})

const passwordLoading = ref(false)
const passwordFormRef = ref<FormInstance>()
const passwordForm = ref<ChangePasswordRequest & { confirm_password: string }>({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const signatureLoading = ref(false)
const uploadRef = ref<UploadInstance>()
const signatureFile = ref<File | null>(null)

const profileRules: FormRules = {
  full_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效邮箱地址', trigger: ['blur', 'change'] }
  ],
  phone: [{ max: 20, message: '电话长度不能超过 20 位', trigger: 'blur' }],
  department: [{ max: 100, message: '部门长度不能超过 100 个字符', trigger: 'blur' }],
  position: [{ max: 100, message: '职位长度不能超过 100 个字符', trigger: 'blur' }]
}

const passwordRules: FormRules = {
  old_password: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能少于 8 位', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        const count = [/[A-Z]/, /[a-z]/, /\d/, /[!@#$%^&*(),.?":{}|<>]/]
          .map((pattern) => pattern.test(value))
          .filter(Boolean).length

        if (count < 3) {
          callback(new Error('密码需包含大写、小写、数字、特殊字符中的至少三类'))
          return
        }

        callback()
      },
      trigger: 'blur'
    }
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== passwordForm.value.new_password) {
          callback(new Error('两次输入的密码不一致'))
          return
        }

        callback()
      },
      trigger: 'blur'
    }
  ]
}

const internalDashboard = computed(() =>
  authStore.isInternal ? (dashboardData.value as InternalDashboard | null) : null
)
const supplierDashboard = computed(() =>
  authStore.isSupplier ? (dashboardData.value as SupplierDashboard | null) : null
)

const featureBlocks = computed(() => dashboardData.value?.feature_blocks || {
  metrics: false,
  announcements: false,
  notifications: false
})
const sessionUser = computed(() => dashboardData.value?.user_info || authStore.userInfo)
const environment = computed(() => dashboardData.value?.environment || authStore.currentEnvironment)
const quickActionContext = computed<WorkbenchQuickActionContext>(() => ({
  isInternal: authStore.isInternal,
  isSupplier: authStore.isSupplier,
  isPlatformAdmin: authStore.isPlatformAdmin,
  isFeatureEnabled: (featureKey: string) => featureFlagStore.isFeatureEnabled(featureKey)
}))
const configurableQuickActions = computed(() =>
  getConfigurableQuickActions(quickActionContext.value)
)
const quickActionGroups = computed(() => {
  const keyword = quickActionKeyword.value.trim()
  const groups = new Map<string, WorkbenchQuickActionOption[]>()

  for (const option of configurableQuickActions.value) {
    const matchesKeyword = !keyword || [option.title, option.description, option.category]
      .some((field) => field.includes(keyword))

    if (!matchesKeyword) {
      continue
    }

    const group = groups.get(option.category) || []
    group.push(option)
    groups.set(option.category, group)
  }

  return Array.from(groups.entries()).map(([category, items]) => ({ category, items }))
})
const quickActions = computed(() =>
  getVisibleQuickActions(
    selectedQuickActionIds.value,
    configurableQuickActions.value,
    quickActionContext.value
  )
)
const taskList = computed<TodoTask[]>(() => {
  if (authStore.isInternal) {
    return internalDashboard.value?.todos || []
  }
  return supplierDashboard.value?.action_required_tasks || []
})

const taskSectionTitle = computed(() => (authStore.isInternal ? '待办任务' : '待处理任务'))
const taskEmptyDescription = computed(() =>
  authStore.isInternal ? '当前没有待办任务' : '当前没有需要处理的任务'
)
const secondaryPanelTitle = computed(() => '通知公告')
const profileDescription = computed(() => {
  if (authStore.isInternal) {
    return [sessionUser.value?.department, sessionUser.value?.position].filter(Boolean).join(' / ') || '内部员工'
  }

  return [sessionUser.value?.supplier_name, sessionUser.value?.position].filter(Boolean).join(' / ') || '供应商账号'
})

const currentSignature = computed(() => toAssetUrl(
  sessionUser.value?.signature_image_path || sessionUser.value?.digital_signature || ''
))
const avatarUrl = computed(() => toAssetUrl(sessionUser.value?.avatar_image_path || ''))
const canEditOwnProfile = computed(() => authStore.isPlatformAdmin)
const settingsPrimaryLabel = computed(() => {
  switch (activeSettingsTab.value) {
    case 'profile':
      return '保存资料'
    case 'avatar':
      return '选择头像'
    case 'password':
      return '确认修改'
    case 'signature':
      return '上传签名'
    default:
      return '保存'
  }
})
const settingsPrimaryLoading = computed(() => {
  switch (activeSettingsTab.value) {
    case 'profile':
      return profileLoading.value
    case 'avatar':
      return avatarLoading.value
    case 'password':
      return passwordLoading.value
    case 'signature':
      return signatureLoading.value
    default:
      return false
  }
})
const settingsPrimaryDisabled = computed(() => {
  if (activeSettingsTab.value === 'profile' && !canEditOwnProfile.value) {
    return true
  }
  return false
})

function syncProfileForm() {
  profileForm.full_name = sessionUser.value?.full_name || ''
  profileForm.email = sessionUser.value?.email || ''
  profileForm.phone = sessionUser.value?.phone || ''
  profileForm.department = sessionUser.value?.department || ''
  profileForm.position = sessionUser.value?.position || ''
}

function syncSessionUserInfo() {
  if (!dashboardData.value || !authStore.userInfo) {
    return
  }

  dashboardData.value = {
    ...dashboardData.value,
    user_info: authStore.userInfo
  } as DashboardData
}

function toAssetUrl(path: string | null | undefined) {
  if (!path) {
    return ''
  }
  if (/^https?:\/\//.test(path)) {
    return path
  }
  return path.startsWith('/api') ? path : `/api${path}`
}

function triggerAvatarUpload() {
  avatarInputRef.value?.click()
}

function resetPasswordForm() {
  passwordForm.value = {
    old_password: '',
    new_password: '',
    confirm_password: ''
  }
}

function resetSignatureForm() {
  signatureFile.value = null
  uploadRef.value?.clearFiles()
}

function prepareSettingsDialog() {
  syncProfileForm()
  resetPasswordForm()
  resetSignatureForm()
}

function openSettingsDialog(tab: SettingsTabName = 'profile') {
  activeSettingsTab.value = tab
  prepareSettingsDialog()
  showSettingsDialog.value = true
}

function handleSettingsPrimaryAction() {
  switch (activeSettingsTab.value) {
    case 'profile':
      void handleUpdateProfile()
      break
    case 'avatar':
      triggerAvatarUpload()
      break
    case 'password':
      void handleChangePassword()
      break
    case 'signature':
      void handleUploadSignature()
      break
  }
}

function handleAvatarFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) {
    return
  }

  const reader = new FileReader()
  reader.onload = (e) => {
    cropperOption.img = (e.target?.result as string) || ''
    activeSettingsTab.value = 'avatar'
    showCropperDialog.value = true
  }
  reader.readAsDataURL(file)
  target.value = ''
}

async function handleCropAndUpload() {
  if (!cropperRef.value) {
    return
  }

  avatarLoading.value = true

  try {
    const blob = await new Promise<Blob>((resolve, reject) => {
      cropperRef.value.getCropBlob((result: Blob | null) => {
        if (!result) {
          reject(new Error('裁剪结果为空'))
          return
        }
        resolve(result)
      })
    })

    await workbenchApi.uploadAvatar(blob)
    await authStore.refreshUserInfo()
    syncSessionUserInfo()
    showCropperDialog.value = false
    ElMessage.success('头像已更新')
  } catch (error: any) {
    ElMessage.error(error.message || '头像上传失败')
  } finally {
    avatarLoading.value = false
  }
}

async function handleUpdateProfile() {
  if (!canEditOwnProfile.value) {
    ElMessage.warning('仅平台管理员可修改账户信息')
    return
  }

  if (!profileFormRef.value) {
    return
  }

  await profileFormRef.value.validate(async (valid) => {
    if (!valid) {
      return
    }

    profileLoading.value = true
    try {
      const payload: ProfileUpdateRequest = {
        full_name: profileForm.full_name.trim(),
        email: profileForm.email.trim(),
        phone: profileForm.phone.trim() || null,
        position: profileForm.position.trim() || null
      }

      if (authStore.isInternal) {
        payload.department = profileForm.department.trim() || null
      }

      await workbenchApi.updateProfile(payload)
      await authStore.refreshUserInfo()
      syncSessionUserInfo()
      syncProfileForm()
      ElMessage.success('账户信息已更新')
    } catch (error: any) {
      ElMessage.error(error.message || '账户信息更新失败')
    } finally {
      profileLoading.value = false
    }
  })
}

async function loadDashboardData() {
  loading.value = true
  try {
    dashboardData.value = await workbenchApi.getDashboardData()
    initializeQuickActions()
  } catch (error: any) {
    ElMessage.error(error.message || '加载工作台数据失败')
  } finally {
    loading.value = false
  }
}

function getQuickActionDefaultIds() {
  const defaultIds = getDefaultQuickActionIds(
    dashboardData.value?.quick_actions || [],
    configurableQuickActions.value
  )

  return sanitizeQuickActionIds(defaultIds, configurableQuickActions.value)
}

function initializeQuickActions() {
  const currentUserId = sessionUser.value?.id || authStore.userInfo?.id
  if (!currentUserId) {
    selectedQuickActionIds.value = []
    quickActionDraft.value = []
    return
  }

  const storageKey = getWorkbenchQuickActionStorageKey(currentUserId)
  const defaultIds = getQuickActionDefaultIds()
  const storedValue = localStorage.getItem(storageKey)

  if (!storedValue) {
    selectedQuickActionIds.value = defaultIds
    quickActionDraft.value = [...defaultIds]
    return
  }

  try {
    const parsed = JSON.parse(storedValue)
    const sanitizedIds = sanitizeQuickActionIds(
      Array.isArray(parsed) ? parsed : [],
      configurableQuickActions.value
    )

    selectedQuickActionIds.value = sanitizedIds.length ? sanitizedIds : defaultIds
    quickActionDraft.value = [...selectedQuickActionIds.value]
  } catch (error) {
    console.error('Failed to parse quick action preferences:', error)
    selectedQuickActionIds.value = defaultIds
    quickActionDraft.value = [...defaultIds]
  }
}

function openQuickActionDialog() {
  quickActionDraft.value = [...selectedQuickActionIds.value]
  quickActionKeyword.value = ''
  showQuickActionDialog.value = true
}

function resetQuickActionsToDefault() {
  quickActionDraft.value = getQuickActionDefaultIds()
}

function isQuickActionSelected(actionId: string) {
  return quickActionDraft.value.includes(actionId)
}

function toggleQuickAction(actionId: string) {
  if (isQuickActionSelected(actionId)) {
    quickActionDraft.value = quickActionDraft.value.filter((id) => id !== actionId)
    return
  }

  quickActionDraft.value = [...quickActionDraft.value, actionId]
}

function saveQuickActions() {
  const currentUserId = sessionUser.value?.id || authStore.userInfo?.id
  const sanitizedIds = sanitizeQuickActionIds(quickActionDraft.value, configurableQuickActions.value)

  selectedQuickActionIds.value = sanitizedIds
  quickActionDraft.value = [...sanitizedIds]

  if (currentUserId) {
    localStorage.setItem(
      getWorkbenchQuickActionStorageKey(currentUserId),
      JSON.stringify(sanitizedIds)
    )
  }

  showQuickActionDialog.value = false
  ElMessage.success('快捷入口配置已保存')
}

function isQuickActionAvailable(option: WorkbenchQuickActionOption) {
  return isQuickActionCurrentlyAvailable(option, quickActionContext.value)
}

async function loadUnreadImportantAnnouncements() {
  if (!featureBlocks.value.announcements) {
    unreadImportantAnnouncements.value = []
    showAnnouncementDialog.value = false
    return
  }

  try {
    const announcements = await announcementApi.getUnreadImportantAnnouncements()
    unreadImportantAnnouncements.value = announcements
    showAnnouncementDialog.value = announcements.length > 0
  } catch (error) {
    console.error('Failed to load unread important announcements:', error)
  }
}

function handleAllAnnouncementsRead() {
  unreadImportantAnnouncements.value = []
  showAnnouncementDialog.value = false
}

function handleTaskClick(task: TodoTask) {
  router.push(task.link)
}

async function handleChangePassword() {
  if (!passwordFormRef.value) {
    return
  }

  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) {
      return
    }

    passwordLoading.value = true
    try {
      await workbenchApi.changePassword({
        old_password: passwordForm.value.old_password,
        new_password: passwordForm.value.new_password
      })
      showSettingsDialog.value = false
      resetPasswordForm()
      ElMessage.success('密码修改成功，请重新登录')
      setTimeout(() => {
        authStore.logout()
        router.push('/login')
      }, 1200)
    } catch (error: any) {
      ElMessage.error(error.message || '密码修改失败')
    } finally {
      passwordLoading.value = false
    }
  })
}

function handleSignatureChange(file: UploadFile) {
  signatureFile.value = file.raw || null
}

function handleExceed() {
  ElMessage.warning('只能上传一个签名文件')
}

async function handleUploadSignature() {
  if (!signatureFile.value) {
    ElMessage.warning('请先选择签名文件')
    return
  }

  signatureLoading.value = true
  try {
    await workbenchApi.uploadSignature(signatureFile.value)
    await authStore.refreshUserInfo()
    syncSessionUserInfo()
    resetSignatureForm()
    ElMessage.success('电子签名已更新')
  } catch (error: any) {
    ElMessage.error(error.message || '签名上传失败')
  } finally {
    signatureLoading.value = false
  }
}

onMounted(async () => {
  await featureFlagStore.loadFeatureFlags()
  await loadDashboardData()
  await loadUnreadImportantAnnouncements()
})
</script>

<style scoped>
.workbench-container {
  padding: 20px;
}

.loading-container {
  padding: 40px;
}

.dashboard-row {
  margin-top: 0;
}

.dashboard-card,
.profile-card {
  margin-bottom: 20px;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 20px;
}

.profile-info {
  flex: 1;
  min-width: 0;
}

.profile-info h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.profile-meta {
  margin: 8px 0 0;
  color: #909399;
  font-size: 14px;
}

.avatar-wrapper {
  position: relative;
  flex-shrink: 0;
  overflow: hidden;
  border-radius: 50%;
  border: 6px solid #f5f8ff;
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.08);
}

.profile-actions {
  display: flex;
  justify-content: flex-end;
}

.profile-main-button {
  min-width: 132px;
  height: 40px;
  padding: 0 18px;
  border-radius: 999px;
  box-shadow: 0 10px 24px rgba(64, 158, 255, 0.18);
}

.cropper-container {
  height: 360px;
  width: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.card-header-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 16px;
  font-weight: 600;
}

.quick-action-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.quick-action-card {
  cursor: pointer;
  border: 1px solid #e4e7ed;
  transition: all 0.2s ease;
}

.quick-action-card:hover {
  border-color: #409eff;
  transform: translateY(-2px);
}

.quick-action-title {
  font-weight: 600;
  color: #303133;
}

.quick-action-config-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.quick-action-config-toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
}

.quick-action-config-toolbar :deep(.el-input) {
  flex: 1;
}

.quick-action-config-summary {
  min-width: 92px;
  color: #606266;
  font-size: 13px;
  text-align: right;
}

.quick-action-group-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-height: 52vh;
  overflow-y: auto;
  padding-right: 4px;
}

.quick-action-group {
  border: 1px solid #ebeef5;
  border-radius: 14px;
  padding: 16px;
}

.quick-action-group__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.quick-action-group__header h4 {
  margin: 0;
  color: #303133;
  font-size: 15px;
}

.quick-action-group__header span {
  color: #909399;
  font-size: 12px;
}

.quick-action-group__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.quick-action-option {
  display: grid;
  grid-template-columns: 24px minmax(0, 1fr);
  align-items: flex-start;
  gap: 12px;
  width: 100%;
  min-width: 0;
  margin-right: 0;
  appearance: none;
  text-align: left;
  font: inherit;
  color: inherit;
  cursor: pointer;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  background: linear-gradient(180deg, #ffffff 0%, #f9fbff 100%);
  padding: 14px;
  transition: all 0.2s ease;
}

.quick-action-option__check {
  display: flex;
  height: 20px;
  width: 20px;
  align-items: center;
  justify-content: center;
  border: 1px solid #d4dbe7;
  border-radius: 6px;
  background: #fff;
  color: transparent;
  transition: all 0.2s ease;
}

.quick-action-option__content {
  display: flex;
  min-height: 24px;
  min-width: 0;
  flex-direction: column;
  justify-content: center;
}

.quick-action-option:hover {
  border-color: #bfd9ff;
  box-shadow: 0 10px 24px rgba(64, 158, 255, 0.08);
  transform: translateY(-1px);
}

.quick-action-option--selected {
  border-color: #409eff;
  background: linear-gradient(180deg, #f7fbff 0%, #ecf5ff 100%);
  box-shadow: 0 12px 30px rgba(64, 158, 255, 0.12);
}

.quick-action-option--selected .quick-action-option__check {
  border-color: #409eff;
  background: #409eff;
  color: #fff;
}

.quick-action-option__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.quick-action-option__title {
  color: #303133;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
}

.announcement-placeholder {
  display: flex;
  min-height: 280px;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  padding: 12px;
}

.system-settings-dialog :deep(.el-dialog__body) {
  padding-top: 12px;
}

.settings-tabs :deep(.el-tabs__header) {
  margin-bottom: 14px;
}

.settings-tabs :deep(.el-tabs__nav-scroll) {
  width: 100%;
}

.settings-tabs :deep(.el-tabs__nav) {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  width: 100%;
}

.settings-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.settings-tabs :deep(.el-tabs__item) {
  display: inline-flex;
  width: 100%;
  align-items: center;
  justify-content: center;
  text-align: center;
  box-sizing: border-box;
  height: 44px;
  padding: 0 12px;
  margin-right: 0;
  border-radius: 999px;
  color: #687385;
  font-size: 13px;
  font-weight: 600;
  line-height: 1;
  transition: all 0.2s ease;
}

.settings-tabs :deep(.el-tabs__item.is-active) {
  background: #edf5ff;
  color: #409eff;
}

.settings-tabs :deep(.el-tabs__active-bar) {
  display: none;
}

.settings-pane {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 360px;
  padding: 4px 2px 2px;
}

.settings-inline-note {
  display: flex;
  align-items: center;
  min-height: 44px;
  padding: 0 14px;
  border-radius: 12px;
  background: #f5f9ff;
  color: #4b6280;
  font-size: 13px;
}

.settings-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.settings-dialog-footer__button {
  min-width: 120px;
  height: 40px;
  margin: 0;
}

.profile-settings-form {
  padding: 4px 2px 0;
}

.avatar-settings-panel {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.avatar-settings-preview {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 18px;
  border-radius: 16px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  border: 1px solid #e6edf8;
}

.avatar-settings-preview__text {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.avatar-settings-preview__text strong {
  color: #1f2a37;
  font-size: 18px;
  font-weight: 700;
}

.avatar-settings-preview__text span {
  color: #6b7280;
  font-size: 13px;
  line-height: 1.7;
}

.avatar-settings-actions {
  display: flex;
  justify-content: flex-end;
}

.metrics-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.metric-item {
  border-radius: 10px;
  background: #f8fafc;
  padding: 14px;
}

.metric-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  gap: 12px;
}

.metric-value {
  font-size: 20px;
}

.metric-value--good {
  color: #67c23a;
}

.metric-value--warning {
  color: #e6a23c;
}

.metric-value--danger {
  color: #f56c6c;
}

.todo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.password-hint {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}

.signature-upload {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 4px 0 12px;
}

.current-signature {
  text-align: center;
  padding: 18px;
  border: 1px solid #e6edf8;
  border-radius: 16px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
}

.current-signature h4 {
  margin: 0 0 12px;
  color: #606266;
  font-size: 14px;
}

.signature-empty {
  border: 1px dashed #dbe5f1;
  border-radius: 16px;
  background: #fbfdff;
}

.signature-preview {
  max-height: 150px;
  max-width: 300px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background: #f5f7fa;
  padding: 8px;
}

@media (max-width: 768px) {
  .workbench-container {
    padding: 12px;
  }

  .profile-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .profile-actions {
    width: 100%;
    justify-content: stretch;
  }

  .settings-tabs :deep(.el-tabs__item) {
    min-width: 0;
    height: 42px;
    padding: 0 8px;
    margin-right: 0;
  }

  .settings-tabs :deep(.el-tabs__nav) {
    gap: 8px;
  }

  .settings-pane {
    min-height: auto;
  }

  .settings-dialog-footer {
    width: 100%;
    justify-content: stretch;
  }

  .settings-dialog-footer__button {
    flex: 1;
  }

  .profile-actions :deep(.el-button) {
    width: 100%;
  }

  .quick-action-config-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .quick-action-config-summary {
    text-align: left;
  }

  .todo-grid,
  .quick-action-grid {
    grid-template-columns: 1fr;
  }

  .quick-action-group__grid {
    grid-template-columns: 1fr;
  }

  .avatar-settings-preview {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
