<template>
  <div class="workbench-container">
    <!-- 重要公告弹窗 -->
    <AnnouncementDialog
      v-model="showAnnouncementDialog"
      :announcements="unreadImportantAnnouncements"
      @all-read="handleAllAnnouncementsRead"
    />

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- 内部员工视图 -->
    <div v-else-if="authStore.isInternal" class="internal-workbench">
      <!-- 个人信息卡片 -->
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
            <h2>{{ authStore.userInfo?.full_name }}</h2>
            <p class="profile-meta">
              {{ authStore.userInfo?.department }} · {{ authStore.userInfo?.position }}
            </p>
          </div>
          <div class="profile-actions">
            <el-button @click="showPasswordDialog = true" size="small">
              <el-icon><Lock /></el-icon>
              修改密码
            </el-button>
            <el-button @click="showSignatureDialog = true" size="small">
              <el-icon><Edit /></el-icon>
              电子签名
            </el-button>
          </div>
        </div>
      </el-card>

      <!-- 指标全景监控（预留接口） -->
      <div class="metrics-section">
        <h3 class="section-title">指标监控</h3>
        <el-row :gutter="20">
          <el-col 
            :xs="24" 
            :sm="12" 
            :md="8" 
            :lg="6" 
            v-for="metric in dashboardData?.metrics || []" 
            :key="metric.key"
          >
            <el-card class="metric-card" shadow="hover">
              <div class="metric-content">
                <h4>{{ metric.name }}</h4>
                <div class="metric-value" :class="`metric-value--${metric.status}`">
                  {{ metric.value }}{{ metric.unit || '' }}
                </div>
                <el-progress 
                  v-if="metric.achievement !== undefined"
                  :percentage="metric.achievement" 
                  :status="metric.status === 'good' ? 'success' : metric.status === 'warning' ? 'warning' : 'exception'"
                />
              </div>
            </el-card>
          </el-col>
        </el-row>
        
        <!-- 预留接口提示 -->
        <el-empty 
          v-if="!dashboardData?.metrics || dashboardData.metrics.length === 0"
          description="指标监控功能预留，待后续开发"
          :image-size="100"
        />
      </div>

      <!-- 待办任务 + 公告栏 并列布局 -->
      <el-row :gutter="20" class="dashboard-row">
        <!-- 待办任务 -->
        <el-col :xs="24" :sm="24" :md="12" :lg="12">
          <el-card class="dashboard-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="card-header-title">待办任务</span>
                <el-badge :value="dashboardData?.todos?.length || 0" class="item" />
              </div>
            </template>
            <div v-if="dashboardData?.todos && dashboardData.todos.length > 0" class="todo-grid">
              <TaskCard 
                v-for="(task, index) in dashboardData.todos" 
                :key="index"
                :task="task"
                @click="handleTaskClick"
              />
            </div>
            <el-empty 
              v-else
              description="暂无待办任务"
              :image-size="80"
            />
          </el-card>
        </el-col>
        <!-- 公告栏 -->
        <el-col :xs="24" :sm="24" :md="12" :lg="12">
          <el-card class="dashboard-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="card-header-title">
                  <el-icon><Bell /></el-icon>
                  公告栏
                </span>
              </div>
            </template>
            <AnnouncementList />
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 供应商视图 -->
    <div v-else-if="authStore.isSupplier" class="supplier-workbench">
      <!-- 个人信息卡片 -->
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
          <div class="profile-info">
            <h2>{{ authStore.userInfo?.full_name }}</h2>
            <p class="profile-meta">
              {{ authStore.userInfo?.supplier_name }} · {{ authStore.userInfo?.position }}
            </p>
          </div>
          <div class="profile-actions">
            <el-button @click="showPasswordDialog = true" size="small">
              <el-icon><Lock /></el-icon>
              修改密码
            </el-button>
            <el-button @click="showSignatureDialog = true" size="small">
              <el-icon><Edit /></el-icon>
              电子签名
            </el-button>
          </div>
        </div>
      </el-card>

      <!-- 绩效红绿灯（预留接口） -->
      <el-card class="performance-card" shadow="hover">
        <template #header>
          <span class="card-header-title">供应商绩效</span>
        </template>
        
        <div v-if="supplierDashboard?.performance_status" class="performance-status">
          <div class="grade-badge" :class="`grade-${supplierDashboard.performance_status.grade}`">
            {{ supplierDashboard.performance_status.grade }}
          </div>
          <div class="score-info">
            <div class="score-item">
              <span class="score-label">当前得分:</span>
              <span class="score-value">{{ supplierDashboard.performance_status.score }}</span>
            </div>
            <div class="score-item deduction">
              <span class="score-label">本月扣分:</span>
              <span class="score-value">{{ supplierDashboard.performance_status.deduction_this_month }}</span>
            </div>
          </div>
        </div>
        
        <el-empty 
          v-else
          description="绩效数据预留，待后续开发"
          :image-size="100"
        />
      </el-card>

      <!-- 待处理任务 + 公告栏 并列 -->
      <el-row :gutter="20" class="dashboard-row">
        <el-col :xs="24" :sm="24" :md="12" :lg="12">
          <el-card class="dashboard-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="card-header-title">待处理任务</span>
                <el-badge :value="supplierDashboard?.action_required_tasks?.length || 0" class="item" />
              </div>
            </template>
            <div v-if="supplierDashboard?.action_required_tasks && supplierDashboard.action_required_tasks.length > 0" class="todo-grid">
              <TaskCard 
                v-for="(task, index) in supplierDashboard.action_required_tasks" 
                :key="index"
                :task="task"
                @click="handleTaskClick"
              />
            </div>
            <el-empty 
              v-else
              description="暂无待处理任务"
              :image-size="80"
            />
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="24" :md="12" :lg="12">
          <el-card class="dashboard-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <span class="card-header-title">
                  <el-icon><Bell /></el-icon>
                  公告栏
                </span>
              </div>
            </template>
            <AnnouncementList />
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 修改密码对话框 -->
    <el-dialog
      v-model="showPasswordDialog"
      title="修改密码"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="100px"
      >
        <el-form-item label="旧密码" prop="old_password">
          <el-input
            v-model="passwordForm.old_password"
            type="password"
            placeholder="请输入旧密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input
            v-model="passwordForm.new_password"
            type="password"
            placeholder="请输入新密码"
            show-password
          />
          <div class="password-hint">
            密码必须包含大写、小写、数字、特殊字符中至少三种，长度大于8位
          </div>
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input
            v-model="passwordForm.confirm_password"
            type="password"
            placeholder="请再次输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPasswordDialog = false">取消</el-button>
        <el-button type="primary" @click="handleChangePassword" :loading="passwordLoading">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 电子签名上传对话框 -->
    <el-dialog
      v-model="showSignatureDialog"
      title="电子签名管理"
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="signature-upload">
        <!-- 当前签名预览 -->
        <div v-if="currentSignature" class="current-signature">
          <h4>当前签名</h4>
          <img :src="currentSignature" alt="电子签名" class="signature-preview" />
        </div>

        <!-- 上传区域 -->
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
          <div class="el-upload__text">
            拖拽文件到此处或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 PNG/JPG 格式，系统将自动处理背景透明化
            </div>
          </template>
        </el-upload>
      </div>
      <template #footer>
        <el-button @click="showSignatureDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUploadSignature" :loading="signatureLoading">
          上传签名
        </el-button>
      </template>
    </el-dialog>

    <!-- 头像裁剪对话框 -->
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
        <el-button type="primary" @click="handleCropAndUpload" :loading="avatarLoading">
          确认上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules, type UploadInstance, type UploadFile } from 'element-plus'
import { User, Lock, Edit, UploadFilled, Bell, Camera } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { workbenchApi } from '@/api/workbench'
import { announcementApi } from '@/api/announcement'
import TaskCard from '@/components/TaskCard.vue'
import AnnouncementDialog from '@/components/AnnouncementDialog.vue'
import AnnouncementList from '@/components/AnnouncementList.vue'
import { VueCropper } from 'vue-cropper'
import 'vue-cropper/dist/index.css'
import type { InternalDashboard, SupplierDashboard, TodoTask, ChangePasswordRequest } from '@/types/workbench'
import type { Announcement } from '@/types/announcement'

const router = useRouter()
const authStore = useAuthStore()

// 状态
const loading = ref(false)
const dashboardData = ref<InternalDashboard | null>(null)
const supplierDashboard = ref<SupplierDashboard | null>(null)

// 公告相关
const showAnnouncementDialog = ref(false)
const unreadImportantAnnouncements = ref<Announcement[]>([])

// 头像裁剪相关
const avatarInputRef = ref<HTMLInputElement>()
const cropperRef = ref<any>()
const showCropperDialog = ref(false)
const avatarLoading = ref(false)
const cropperOption = reactive({
  img: '' as string,
  outputSize: 1,
  outputType: 'png'
})

// 修改密码相关
const showPasswordDialog = ref(false)
const passwordLoading = ref(false)
const passwordFormRef = ref<FormInstance>()
const passwordForm = ref<ChangePasswordRequest & { confirm_password: string }>({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

// 密码验证规则
const passwordRules: FormRules = {
  old_password: [
    { required: true, message: '请输入旧密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能少于8位', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        const hasUpper = /[A-Z]/.test(value)
        const hasLower = /[a-z]/.test(value)
        const hasNumber = /\d/.test(value)
        const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(value)
        const count = [hasUpper, hasLower, hasNumber, hasSpecial].filter(Boolean).length
        
        if (count < 3) {
          callback(new Error('密码必须包含大写、小写、数字、特殊字符中至少三种'))
        } else {
          callback()
        }
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
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 电子签名相关
const showSignatureDialog = ref(false)
const signatureLoading = ref(false)
const uploadRef = ref<UploadInstance>()
const signatureFile = ref<File | null>(null)
const currentSignature = computed(() => {
  if (authStore.userInfo?.signature_image_path) {
    // 假设后端返回相对路径，需要拼接完整URL
    return `/api${authStore.userInfo.signature_image_path}`
  }
  return null
})

// 头像URL
const avatarUrl = computed(() => {
  if (authStore.userInfo?.avatar_image_path) {
    return `/api${authStore.userInfo.avatar_image_path}`
  }
  return ''
})

/**
 * 触发头像文件选择
 */
function triggerAvatarUpload() {
  avatarInputRef.value?.click()
}

/**
 * 处理头像文件选择，打开裁剪弹窗
 */
function handleAvatarFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  
  // 读取为 data URL 给 cropper 使用
  const reader = new FileReader()
  reader.onload = (e) => {
    cropperOption.img = e.target?.result as string
    showCropperDialog.value = true
  }
  reader.readAsDataURL(file)
  
  // 清空 input 以便重复选择同一文件
  target.value = ''
}

/**
 * 裁剪并上传头像
 */
async function handleCropAndUpload() {
  if (!cropperRef.value) return
  
  avatarLoading.value = true
  try {
    // 从 cropper 获取裁剪后的 Blob
    cropperRef.value.getCropBlob((blob: Blob) => {
      uploadAvatarBlob(blob)
    })
  } catch (error: any) {
    avatarLoading.value = false
    ElMessage.error('裁剪失败，请重试')
  }
}

/**
 * 上传裁剪后的头像 Blob
 */
async function uploadAvatarBlob(blob: Blob) {
  try {
    await workbenchApi.uploadAvatar(blob)
    ElMessage.success('头像更新成功')
    
    // 刷新用户信息以更新头像
    await authStore.refreshUserInfo()
    
    showCropperDialog.value = false
  } catch (error: any) {
    console.error('Failed to upload avatar:', error)
    ElMessage.error(error.message || '头像上传失败')
  } finally {
    avatarLoading.value = false
  }
}

/**
 * 加载工作台数据
 */
async function loadDashboardData() {
  loading.value = true
  try {
    const data = await workbenchApi.getDashboardData()
    
    if (authStore.isInternal) {
      dashboardData.value = data as InternalDashboard
    } else if (authStore.isSupplier) {
      supplierDashboard.value = data as SupplierDashboard
    }
  } catch (error: any) {
    console.error('Failed to load dashboard data:', error)
    ElMessage.error(error.message || '加载工作台数据失败')
  } finally {
    loading.value = false
  }
}

/**
 * 加载未读重要公告
 */
async function loadUnreadImportantAnnouncements() {
  try {
    const announcements = await announcementApi.getUnreadImportantAnnouncements()
    
    if (announcements && announcements.length > 0) {
      unreadImportantAnnouncements.value = announcements
      showAnnouncementDialog.value = true
    }
  } catch (error: any) {
    console.error('Failed to load unread important announcements:', error)
    // 不显示错误消息，避免干扰用户体验
  }
}

/**
 * 处理所有公告已读
 */
function handleAllAnnouncementsRead() {
  unreadImportantAnnouncements.value = []
  ElMessage.success('所有重要公告已阅读完毕')
}

/**
 * 处理任务点击
 */
function handleTaskClick(task: TodoTask) {
  // 跳转到对应的单据详情页
  router.push(task.link)
}

/**
 * 处理修改密码
 */
async function handleChangePassword() {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    passwordLoading.value = true
    try {
      await workbenchApi.changePassword({
        old_password: passwordForm.value.old_password,
        new_password: passwordForm.value.new_password
      })
      
      ElMessage.success('密码修改成功，请重新登录')
      
      // 关闭对话框
      showPasswordDialog.value = false
      
      // 清空表单
      passwordForm.value = {
        old_password: '',
        new_password: '',
        confirm_password: ''
      }
      
      // 延迟后登出
      setTimeout(() => {
        authStore.logout()
        router.push('/login')
      }, 1500)
    } catch (error: any) {
      console.error('Failed to change password:', error)
      ElMessage.error(error.message || '密码修改失败')
    } finally {
      passwordLoading.value = false
    }
  })
}

/**
 * 处理签名文件变化
 */
function handleSignatureChange(file: UploadFile) {
  signatureFile.value = file.raw || null
}

/**
 * 处理文件超出限制
 */
function handleExceed() {
  ElMessage.warning('只能上传一个签名文件')
}

/**
 * 上传电子签名
 */
async function handleUploadSignature() {
  if (!signatureFile.value) {
    ElMessage.warning('请选择要上传的签名文件')
    return
  }
  
  signatureLoading.value = true
  try {
    const response = await workbenchApi.uploadSignature(signatureFile.value)
    
    ElMessage.success(response.message || '电子签名上传成功')
    
    // 刷新用户信息
    await authStore.refreshUserInfo()
    
    // 关闭对话框
    showSignatureDialog.value = false
    
    // 清空文件
    signatureFile.value = null
    uploadRef.value?.clearFiles()
  } catch (error: any) {
    console.error('Failed to upload signature:', error)
    ElMessage.error(error.message || '电子签名上传失败')
  } finally {
    signatureLoading.value = false
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadDashboardData()
  loadUnreadImportantAnnouncements()
})
</script>

<style scoped>
.workbench-container {
  padding: 20px;
}

.loading-container {
  padding: 40px;
}

/* 头像上传 */
.avatar-wrapper {
  position: relative;
  cursor: pointer;
  border-radius: 50%;
  overflow: hidden;
}

.avatar-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 20px;
  opacity: 0;
  transition: opacity 0.3s;
  border-radius: 50%;
}

.avatar-wrapper:hover .avatar-overlay {
  opacity: 1;
}

/* 裁剪弹窗 */
.cropper-container {
  width: 100%;
  height: 360px;
}

/* 仪表盘并列卡片 */
.dashboard-row {
  margin-top: 0;
}

.dashboard-card {
  min-height: 300px;
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-header-title {
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 个人信息卡片 */
.profile-card {
  margin-bottom: 24px;
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
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.profile-meta {
  margin: 0;
  font-size: 14px;
  color: #909399;
}

.profile-actions {
  display: flex;
  gap: 8px;
}

/* 章节标题 */
.section-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 指标卡片 */
.metrics-section {
  margin-bottom: 24px;
}

.metric-card {
  margin-bottom: 16px;
  height: 100%;
}

.metric-content h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.metric-value {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 12px;
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

/* 待办任务 */
.todo-section,
.action-required-section {
  margin-bottom: 24px;
}

.todo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

/* 供应商绩效卡片 */
.performance-card {
  margin-bottom: 24px;
}

.card-header-title {
  font-size: 16px;
  font-weight: 600;
}

.performance-status {
  display: flex;
  align-items: center;
  gap: 24px;
}

.grade-badge {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  font-weight: bold;
  color: white;
}

.grade-A {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
}

.grade-B {
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
}

.grade-C {
  background: linear-gradient(135deg, #e6a23c 0%, #ebb563 100%);
}

.grade-D {
  background: linear-gradient(135deg, #f56c6c 0%, #f78989 100%);
}

.score-info {
  flex: 1;
}

.score-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.score-label {
  font-size: 14px;
  color: #606266;
}

.score-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.score-item.deduction .score-value {
  color: #f56c6c;
}

/* 密码提示 */
.password-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

/* 签名上传 */
.signature-upload {
  padding: 20px 0;
}

.current-signature {
  margin-bottom: 24px;
  text-align: center;
}

.current-signature h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #606266;
}

.signature-preview {
  max-width: 300px;
  max-height: 150px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 8px;
  background: #f5f7fa;
}

.signature-uploader {
  width: 100%;
}

/* 移动端适配 */
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

  .profile-actions .el-button {
    width: 100%;
  }

  .todo-grid {
    grid-template-columns: 1fr;
  }

  .performance-status {
    flex-direction: column;
    align-items: flex-start;
  }

  .grade-badge {
    width: 60px;
    height: 60px;
    font-size: 28px;
  }
}
</style>
