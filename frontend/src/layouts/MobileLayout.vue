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
        <el-menu-item index="/workbench">
          <el-icon><HomeFilled /></el-icon>
          <template #title>工作台</template>
        </el-menu-item>
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
import { Menu, User, HomeFilled } from '@element-plus/icons-vue'
import { useEnvironment } from '@/composables/useEnvironment'

const router = useRouter()
const route = useRoute()

const drawerVisible = ref(false)
const showUserMenu = ref(false)
const userInfo = ref<any>(null)

// 使用环境管理 composable
const { isPreview, switchButtonText, switchEnvironment } = useEnvironment()

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
  localStorage.removeItem('access_token')
  localStorage.removeItem('user_info')
  showUserMenu.value = false
  router.push('/login')
}

onMounted(() => {
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
