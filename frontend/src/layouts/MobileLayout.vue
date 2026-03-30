<template>
  <div class="mobile-layout">
    <!-- 顶部导航栏 -->
    <div class="mobile-header">
      <div class="header-left">
        <el-icon class="menu-icon" @click="toggleDrawer">
          <Menu />
        </el-icon>
        <span class="logo">QMS</span>
        <span class="environment-badge" v-if="isPreview">预览版</span>
      </div>
      <div class="header-right">
        <el-icon class="user-icon" @click="showUserMenu = true">
          <User />
        </el-icon>
      </div>
    </div>

    <!-- 内容区域 -->
    <div class="mobile-content">
      <slot />
    </div>

    <!-- 侧边抽屉菜单 -->
    <el-drawer
      v-model="drawerVisible"
      direction="ltr"
      :size="280"
      title="菜单"
    >
      <el-menu
        :default-active="activeMenu"
        router
        @select="handleMenuSelect"
      >
        <!-- 2.2 个人中心 -->
        <el-menu-item index="/workbench">
          <el-icon><HomeFilled /></el-icon>
          <template #title>工作台</template>
        </el-menu-item>

        <!-- 2.4 质量数据面板 -->
        <el-sub-menu index="quality-data">
          <template #title>
            <el-icon><DataLine /></el-icon>
            <span>质量数据面板</span>
          </template>
          <el-menu-item index="/quality-dashboard">数据仪表盘</el-menu-item>
          <el-menu-item index="/quality-dashboard/analysis">专项数据分析</el-menu-item>
        </el-sub-menu>

        <!-- 2.5 供应商质量管理 -->
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

        <!-- 2.6 过程质量管理 -->
        <el-sub-menu index="process-quality">
          <template #title>
            <el-icon><Monitor /></el-icon>
            <span>过程质量管理</span>
          </template>
          <el-menu-item index="/quality/process-defects">不合格品数据</el-menu-item>
          <el-menu-item index="/quality/process-issues">过程问题管理</el-menu-item>
        </el-sub-menu>

        <!-- 2.7 客户质量管理 -->
        <el-sub-menu index="customer-quality">
          <template #title>
            <el-icon><UserFilled /></el-icon>
            <span>客户质量管理</span>
          </template>
          <el-menu-item index="/quality/customer-complaints">客诉管理</el-menu-item>
          <el-menu-item index="/quality/eight-d-customer">客户8D报告</el-menu-item>
          <el-menu-item index="/quality/customer-claims">客户索赔</el-menu-item>
        </el-sub-menu>

        <!-- 2.8 新品质量管理 -->
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

        <!-- 2.9 审核管理 -->
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

        <!-- 2.3 系统管理 -->
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
      </el-menu>
    </el-drawer>

    <!-- 用户菜单弹窗 -->
    <el-dialog
      v-model="showUserMenu"
      title="用户菜单"
      width="90%"
      :show-close="true"
    >
      <div class="user-menu-content">
        <div class="user-info-section">
          <el-icon class="user-avatar"><User /></el-icon>
          <div class="user-name">{{ userInfo?.full_name || '用户' }}</div>
        </div>
        <el-divider />
        <el-button type="primary" @click="switchEnvironment" class="menu-button">
          {{ switchButtonText }}
        </el-button>
        <el-button @click="goToProfile" class="menu-button">个人中心</el-button>
        <el-button type="danger" @click="handleLogout" class="menu-button">退出登录</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { 
  Menu, User, HomeFilled, OfficeBuilding, DataLine, 
  Document, Opportunity, Setting, Monitor, UserFilled
} from '@element-plus/icons-vue'
import { useEnvironment } from '@/composables/useEnvironment'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const drawerVisible = ref(false)
const showUserMenu = ref(false)
const userInfo = ref<any>(null)

// 使用环境管理 composable
const { isPreview, switchButtonText, switchEnvironment, syncEnvironmentState } = useEnvironment()

// 当前激活的菜单
const activeMenu = computed(() => route.path)

// 切换抽屉
const toggleDrawer = () => {
  drawerVisible.value = !drawerVisible.value
}

// 菜单选择后关闭抽屉
const handleMenuSelect = () => {
  drawerVisible.value = false
}

// 前往个人中心
const goToProfile = () => {
  showUserMenu.value = false
  router.push('/profile')
}

// 退出登录
const handleLogout = () => {
  authStore.logout()
  showUserMenu.value = false
  router.push('/login')
}

onMounted(() => {
  syncEnvironmentState()
  // 加载用户信息
  const userInfoStr = localStorage.getItem('user_info')
  if (userInfoStr) {
    userInfo.value = JSON.parse(userInfoStr)
  }
})
</script>

<style scoped>
.mobile-layout {
  width: 100%;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.mobile-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 56px;
  background-color: #409eff;
  color: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 16px;
  z-index: 1000;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.menu-icon,
.user-icon {
  font-size: 24px;
  cursor: pointer;
  /* 放大触控区域 */
  padding: 8px;
  margin: -8px;
}

.logo {
  font-size: 20px;
  font-weight: bold;
}

.environment-badge {
  background-color: #f56c6c;
  color: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.mobile-content {
  margin-top: 56px;
  padding: 16px;
  flex: 1;
  background-color: #f0f2f5;
}

.user-menu-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.user-info-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 0;
}

.user-avatar {
  font-size: 48px;
  color: #409eff;
}

.user-name {
  font-size: 18px;
  font-weight: bold;
}

.menu-button {
  width: 100%;
  /* 放大按钮高度以适应手指触控 */
  height: 48px;
  font-size: 16px;
  /* 增加触控区域 */
  min-height: 44px;
}

/* 移动端输入框放大 */
:deep(.el-input__inner) {
  height: 44px !important;
  font-size: 16px !important;
}

/* 移动端按钮放大 */
:deep(.el-button) {
  min-height: 44px;
  font-size: 16px;
  padding: 12px 20px;
}
</style>
