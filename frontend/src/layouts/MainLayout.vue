<template>
  <div class="main-layout">
    <!-- 桌面端布局 -->
    <el-container v-if="!isMobile" class="desktop-layout">
      <!-- 侧边栏 -->
      <el-aside :width="isCollapse ? '64px' : '220px'" class="sidebar">
        <div class="logo">
          <span v-if="!isCollapse">QMS</span>
          <span v-else>Q</span>
        </div>
        <el-scrollbar>
          <el-menu
            :default-active="activeMenu"
            :collapse="isCollapse"
            router
            background-color="#304156"
            text-color="#bfcbd9"
            active-text-color="#409EFF"
          >
            <!-- ========== 2.2 个人中心 ========== -->
            <el-menu-item index="/workbench">
              <el-icon><HomeFilled /></el-icon>
              <template #title>工作台</template>
            </el-menu-item>

            <!-- ========== 2.4 质量数据面板 ========== -->
            <el-sub-menu index="quality-data">
              <template #title>
                <el-icon><DataLine /></el-icon>
                <span>质量数据面板</span>
              </template>
              <el-menu-item index="/quality-dashboard">数据仪表盘</el-menu-item>
              <el-menu-item index="/quality-dashboard/analysis">专项数据分析</el-menu-item>
            </el-sub-menu>

            <!-- ========== 2.5 供应商质量管理 ========== -->
            <el-sub-menu index="supplier">
              <template #title>
                <el-icon><OfficeBuilding /></el-icon>
                <span>供应商质量管理</span>
              </template>
              <el-menu-item index="/supplier/scar">SCAR管理</el-menu-item>
              <el-menu-item index="/supplier/eight-d">供应商8D报告</el-menu-item>
              <el-menu-item index="/supplier/audit-plan">供应商审核</el-menu-item>
              <el-menu-item index="/supplier/targets">目标管理</el-menu-item>
              <el-menu-item index="/supplier/performance">绩效评价</el-menu-item>
              <el-menu-item index="/supplier/meetings">供应商会议</el-menu-item>
              <el-menu-item index="/supplier/ppap">PPAP管理</el-menu-item>
              <el-menu-item index="/supplier/inspection-specs">检验规范</el-menu-item>
              <el-menu-item index="/supplier/barcode">防错扫码</el-menu-item>
              <el-menu-item index="/supplier/claims">供应商索赔</el-menu-item>
              <el-menu-item index="/supplier/change-management">供应商变更</el-menu-item>
            </el-sub-menu>

            <!-- ========== 2.6 过程质量管理 ========== -->
            <el-sub-menu index="process-quality">
              <template #title>
                <el-icon><Monitor /></el-icon>
                <span>过程质量管理</span>
              </template>
              <el-menu-item index="/quality/process-defects">不合格品数据</el-menu-item>
              <el-menu-item index="/quality/process-issues">过程问题管理</el-menu-item>
            </el-sub-menu>

            <!-- ========== 2.7 客户质量管理 ========== -->
            <el-sub-menu index="customer-quality">
              <template #title>
                <el-icon><UserFilled /></el-icon>
                <span>客户质量管理</span>
              </template>
              <el-menu-item index="/quality/customer-complaints">客诉管理</el-menu-item>
              <el-menu-item index="/quality/eight-d-customer">客户8D报告</el-menu-item>
              <el-menu-item index="/quality/customer-claims">客户索赔</el-menu-item>
            </el-sub-menu>

            <!-- ========== 2.8 新品质量管理 ========== -->
            <el-sub-menu index="newproduct">
              <template #title>
                <el-icon><Opportunity /></el-icon>
                <span>新品质量管理</span>
              </template>
              <el-menu-item index="/quality/lesson-learned">经验教训库</el-menu-item>
              <el-menu-item index="/newproduct/projects">项目管理</el-menu-item>
              <el-menu-item index="/newproduct/stage-review">阶段评审</el-menu-item>
              <el-menu-item index="/newproduct/lesson-check">经验教训检查</el-menu-item>
              <el-menu-item index="/newproduct/trial">试产管理</el-menu-item>
              <el-menu-item index="/newproduct/trial-issues">试产问题</el-menu-item>
              <el-menu-item index="/newproduct/trial-summary">试产总结</el-menu-item>
            </el-sub-menu>

            <!-- ========== 2.9 审核管理 ========== -->
            <el-sub-menu index="audit">
              <template #title>
                <el-icon><Document /></el-icon>
                <span>审核管理</span>
              </template>
              <el-menu-item index="/audit/plans">审核计划</el-menu-item>
              <el-menu-item index="/audit/templates">审核模板</el-menu-item>
              <el-menu-item index="/audit/execution">审核执行</el-menu-item>
              <el-menu-item index="/audit/nc-list">不符合项</el-menu-item>
              <el-menu-item index="/audit/report">审核报告</el-menu-item>
              <el-menu-item index="/audit/customer">客户审核</el-menu-item>
            </el-sub-menu>

            <!-- ========== 2.3 系统管理（仅管理员可见） ========== -->
            <el-sub-menu index="admin">
              <template #title>
                <el-icon><Setting /></el-icon>
                <span>系统管理</span>
              </template>
              <el-menu-item index="/admin/users">用户管理</el-menu-item>
              <el-menu-item index="/admin/permissions">权限管理</el-menu-item>
              <el-menu-item index="/admin/tasks">任务监控</el-menu-item>
              <el-menu-item index="/admin/operation-logs">操作日志</el-menu-item>
              <el-menu-item index="/admin/feature-flags">功能开关</el-menu-item>
            </el-sub-menu>

            <!-- ========== 2.10 & 2.11 预留功能 ========== -->
            <el-menu-item 
              v-if="isInstrumentsEnabled" 
              index="/instruments"
            >
              <el-icon><Tools /></el-icon>
              <template #title>仪器量具管理</template>
            </el-menu-item>

            <el-menu-item 
              v-if="isQualityCostsEnabled" 
              index="/quality-costs"
            >
              <el-icon><Money /></el-icon>
              <template #title>质量成本管理</template>
            </el-menu-item>
          </el-menu>
        </el-scrollbar>
      </el-aside>

      <!-- 主内容区 -->
      <el-container>
        <!-- 顶部导航栏 -->
        <el-header class="header">
          <div class="header-left">
            <el-icon class="collapse-icon" @click="toggleCollapse">
              <Fold v-if="!isCollapse" />
              <Expand v-else />
            </el-icon>
          </div>
          <div class="header-right">
            <!-- 环境标识徽章 -->
            <span :class="['env-badge', isPreviewEnv ? 'env-badge--preview' : 'env-badge--stable']">
              <span v-if="isPreviewEnv" class="env-dot"></span>
              {{ currentEnvLabel }}
            </span>
            <el-dropdown @command="handleCommand">
              <span class="user-info">
                <el-icon><User /></el-icon>
                <span>{{ userInfo?.full_name || '用户' }}</span>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                  <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>

        <!-- 内容区域 -->
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>

    <!-- 移动端布局 -->
    <MobileLayout v-else>
      <router-view />
    </MobileLayout>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  HomeFilled, User, Fold, Expand, Tools, Money,
  OfficeBuilding, DataLine, Document, 
  Opportunity, Setting, Monitor, UserFilled
} from '@element-plus/icons-vue'
import MobileLayout from './MobileLayout.vue'
import { useFeatureFlagStore } from '@/stores/featureFlag'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const featureFlagStore = useFeatureFlagStore()
const authStore = useAuthStore()

const isCollapse = ref(false)
const isMobile = ref(false)
const userInfo = ref<any>(null)

// 从 auth store 获取环境信息
const isPreviewEnv = computed(() => authStore.isPreviewEnv)
const currentEnvLabel = computed(() => isPreviewEnv.value ? '🧪 预览版' : '🏢 正式版')




// 当前激活的菜单
const activeMenu = computed(() => route.path)

// 检查功能是否启用
const isInstrumentsEnabled = computed(() => 
  featureFlagStore.isFeatureEnabled('instruments.management')
)

const isQualityCostsEnabled = computed(() => 
  featureFlagStore.isFeatureEnabled('quality_costs.management')
)

// 切换侧边栏折叠状态
const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

// 处理用户菜单命令
const handleCommand = (command: string) => {
  if (command === 'logout') {
    authStore.logout()
    router.push('/login')
  } else if (command === 'profile') {
    router.push('/workbench')
  }
}

// 检测屏幕尺寸
const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  
  // 加载用户信息
  const userInfoStr = localStorage.getItem('user_info')
  if (userInfoStr) {
    userInfo.value = JSON.parse(userInfoStr)
  }

  // 加载功能开关配置
  await featureFlagStore.loadFeatureFlags()
})
</script>

<style scoped>
.main-layout {
  width: 100%;
  height: 100vh;
}

.desktop-layout {
  height: 100%;
}

.sidebar {
  background-color: #304156;
  color: #fff;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
}

.sidebar :deep(.el-scrollbar) {
  flex: 1;
  overflow: hidden;
}

.sidebar :deep(.el-menu) {
  border-right: none;
}

/* 子菜单标题样式 */
.sidebar :deep(.el-sub-menu__title) {
  color: #bfcbd9 !important;
}

.sidebar :deep(.el-sub-menu__title:hover) {
  background-color: #263445 !important;
}

/* 子菜单弹出层暗色背景 */
.sidebar :deep(.el-menu--inline) {
  background-color: #1f2d3d !important;
}

.sidebar :deep(.el-menu--inline .el-menu-item) {
  background-color: #1f2d3d !important;
  color: #bfcbd9 !important;
  padding-left: 50px !important;
  min-width: auto;
}

.sidebar :deep(.el-menu--inline .el-menu-item:hover) {
  background-color: #001528 !important;
}

.sidebar :deep(.el-menu--inline .el-menu-item.is-active) {
  color: #409EFF !important;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: bold;
  color: #fff;
  background-color: #2b3a4a;
  flex-shrink: 0;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-icon {
  font-size: 20px;
  cursor: pointer;
}

.environment-badge {
  background-color: #f56c6c;
  color: #fff;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
}

/* 环境标识样式 */
.env-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1;
}

.env-badge--stable {
  background-color: #ecf5ff;
  color: #409eff;
  border: 1px solid #b3d8ff;
}

.env-badge--preview {
  background-color: #fdf6ec;
  color: #e6a23c;
  border: 1px solid #f5dab1;
}

/* 预览版闪烁小圆点 */
.env-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  background-color: #e6a23c;
  border-radius: 50%;
  animation: env-dot-blink 1.2s ease-in-out infinite;
}

@keyframes env-dot-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.2; }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.main-content {
  background-color: #f0f2f5;
  padding: 20px;
}
</style>
