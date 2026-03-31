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
          <div class="avatar-wrapper" @click="triggerAvatarUpload">
            <el-avatar :size="64" :src="avatarUrl">
              <el-icon><User /></el-icon>
            </el-avatar>
            <div class="avatar-overlay">
              <el-icon><Camera /></el-icon>
            </div>
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
            <el-button size="small" @click="showPasswordDialog = true">
              <el-icon><Lock /></el-icon>
              修改密码
            </el-button>
            <el-button size="small" @click="showSignatureDialog = true">
              <el-icon><Edit /></el-icon>
              电子签名
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
                <div class="quick-action-desc">{{ action.description }}</div>
              </el-card>
            </div>
            <el-empty v-else description="当前没有可用的快捷入口" :image-size="90" />
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
            <template v-else-if="authStore.isSupplier">
              <div class="supplier-status">
                <div class="status-row">
                  <span>供应商</span>
                  <strong>{{ sessionUser?.supplier_name || '未关联' }}</strong>
                </div>
                <div class="status-row">
                  <span>当前环境</span>
                  <strong>{{ environment === 'stable' ? '正式环境' : '预览环境' }}</strong>
                </div>
                <div class="status-row">
                  <span>说明</span>
                  <strong>绩效和跨业务卡片将在真实数据源接入后开启</strong>
                </div>
              </div>
            </template>
            <template v-else>
              <el-empty description="公告能力未启用，当前显示基础空态。" :image-size="90" />
            </template>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <el-dialog
      v-model="showPasswordDialog"
      title="修改密码"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form ref="passwordFormRef" :model="passwordForm" :rules="passwordRules" label-width="100px">
        <el-form-item label="旧密码" prop="old_password">
          <el-input v-model="passwordForm.old_password" type="password" show-password placeholder="请输入旧密码" />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input v-model="passwordForm.new_password" type="password" show-password placeholder="请输入新密码" />
          <div class="password-hint">密码需至少 8 位，并包含大写、小写、数字、特殊字符中的三类。</div>
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input v-model="passwordForm.confirm_password" type="password" show-password placeholder="请再次输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPasswordDialog = false">取消</el-button>
        <el-button type="primary" :loading="passwordLoading" @click="handleChangePassword">确认</el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="showSignatureDialog"
      title="电子签名管理"
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="signature-upload">
        <div v-if="currentSignature" class="current-signature">
          <h4>当前签名</h4>
          <img :src="currentSignature" alt="电子签名" class="signature-preview" />
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
      <template #footer>
        <el-button @click="showSignatureDialog = false">取消</el-button>
        <el-button type="primary" :loading="signatureLoading" @click="handleUploadSignature">上传签名</el-button>
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
import { Bell, Camera, Edit, Lock, UploadFilled, User } from '@element-plus/icons-vue'
import { VueCropper } from 'vue-cropper'
import 'vue-cropper/dist/index.css'
import { announcementApi } from '@/api/announcement'
import { workbenchApi } from '@/api/workbench'
import AnnouncementDialog from '@/components/AnnouncementDialog.vue'
import AnnouncementList from '@/components/AnnouncementList.vue'
import TaskCard from '@/components/TaskCard.vue'
import { useAuthStore } from '@/stores/auth'
import type { Announcement } from '@/types/announcement'
import type {
  ChangePasswordRequest,
  DashboardData,
  InternalDashboard,
  SupplierDashboard,
  TodoTask
} from '@/types/workbench'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const dashboardData = ref<DashboardData | null>(null)

const showAnnouncementDialog = ref(false)
const unreadImportantAnnouncements = ref<Announcement[]>([])

const avatarInputRef = ref<HTMLInputElement>()
const cropperRef = ref<any>()
const showCropperDialog = ref(false)
const avatarLoading = ref(false)
const cropperOption = reactive({
  img: '',
  outputSize: 1,
  outputType: 'png'
})

const showPasswordDialog = ref(false)
const passwordLoading = ref(false)
const passwordFormRef = ref<FormInstance>()
const passwordForm = ref<ChangePasswordRequest & { confirm_password: string }>({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const showSignatureDialog = ref(false)
const signatureLoading = ref(false)
const uploadRef = ref<UploadInstance>()
const signatureFile = ref<File | null>(null)

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
const quickActions = computed(() => dashboardData.value?.quick_actions || [])
const sessionUser = computed(() => dashboardData.value?.user_info || authStore.userInfo)
const environment = computed(() => dashboardData.value?.environment || authStore.currentEnvironment)
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
const secondaryPanelTitle = computed(() => (featureBlocks.value.announcements ? '公告栏' : '基础说明'))
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

function handleAvatarFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) {
    return
  }

  const reader = new FileReader()
  reader.onload = (e) => {
    cropperOption.img = (e.target?.result as string) || ''
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
    showCropperDialog.value = false
    ElMessage.success('头像已更新')
  } catch (error: any) {
    ElMessage.error(error.message || '头像上传失败')
  } finally {
    avatarLoading.value = false
  }
}

async function loadDashboardData() {
  loading.value = true
  try {
    dashboardData.value = await workbenchApi.getDashboardData()
  } catch (error: any) {
    ElMessage.error(error.message || '加载工作台数据失败')
  } finally {
    loading.value = false
  }
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
      showPasswordDialog.value = false
      passwordForm.value = {
        old_password: '',
        new_password: '',
        confirm_password: ''
      }
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
    showSignatureDialog.value = false
    signatureFile.value = null
    uploadRef.value?.clearFiles()
    ElMessage.success('电子签名已更新')
  } catch (error: any) {
    ElMessage.error(error.message || '签名上传失败')
  } finally {
    signatureLoading.value = false
  }
}

onMounted(async () => {
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
  gap: 16px;
}

.profile-info {
  flex: 1;
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

.profile-actions {
  display: flex;
  gap: 8px;
}

.avatar-wrapper {
  position: relative;
  cursor: pointer;
  overflow: hidden;
  border-radius: 50%;
}

.avatar-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.4);
  color: #fff;
  font-size: 20px;
  opacity: 0;
  transition: opacity 0.3s;
}

.avatar-wrapper:hover .avatar-overlay {
  opacity: 1;
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

.quick-action-desc {
  margin-top: 8px;
  font-size: 13px;
  line-height: 1.6;
  color: #909399;
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

.supplier-status {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.status-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 12px;
  font-size: 14px;
}

.password-hint {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}

.signature-upload {
  padding: 20px 0;
}

.current-signature {
  margin-bottom: 24px;
  text-align: center;
}

.current-signature h4 {
  margin: 0 0 12px;
  color: #606266;
  font-size: 14px;
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
    flex-direction: column;
  }

  .profile-actions :deep(.el-button) {
    width: 100%;
  }

  .todo-grid,
  .quick-action-grid {
    grid-template-columns: 1fr;
  }

  .status-row {
    flex-direction: column;
  }
}
</style>
