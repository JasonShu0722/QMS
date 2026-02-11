<template>
  <div class="main-layout">
    <!-- 桌面端布局 -->
    <el-container v-if="!isMobile" class="desktop-layout">
      <!-- 侧边栏 -->
      <el-aside :width="isCollapse ? '64px' : '200px'" class="sidebar">
        <div class="logo">
          <span v-if="!isCollapse">QMS</span>
          <span v-else>Q</span>
        </div>
        <el-menu
          :default-active="activeMenu"
          :collapse="isCollapse"
          router
        >
          <el-menu-item index="/workbench">
            <el-icon><HomeFilled /></el-icon>
            <template #title>工作台</template>
          </el-menu-item>
        </el-menu>
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
            <span class="environment-badge" v-if="isPreview">预览版</span>
          </div>
          <div class="header-right">
            <el-button link @click="switchEnvironment">
              {{ isPreview ? '切换到正式版' : '切换到预览版' }}
            </el-button>
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
import { HomeFilled, User, Fold, Expand } from '@element-plus/icons-vue'
import MobileLayout from './MobileLayout.vue'

const router = useRouter()
const route = useRoute()

const isCollapse = ref(false)
const isMobile = ref(false)
const userInfo = ref<any>(null)

// 判断是否为预览环境
const isPreview = computed(() => {
  return window.location.hostname.includes('preview')
})

// 当前激活的菜单
const activeMenu = computed(() => route.path)

// 切换侧边栏折叠状态
const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

// 切换环境
const switchEnvironment = () => {
  const currentHost = window.location.hostname
  if (isPreview.value) {
    // 切换到正式环境
    window.location.href = window.location.href.replace('preview.', '')
  } else {
    // 切换到预览环境
    window.location.href = window.location.href.replace(currentHost, `preview.${currentHost}`)
  }
}

// 处理用户菜单命令
const handleCommand = (command: string) => {
  if (command === 'logout') {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_info')
    router.push('/login')
  } else if (command === 'profile') {
    router.push('/profile')
  }
}

// 检测屏幕尺寸
const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  
  // 加载用户信息
  const userInfoStr = localStorage.getItem('user_info')
  if (userInfoStr) {
    userInfo.value = JSON.parse(userInfoStr)
  }
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
