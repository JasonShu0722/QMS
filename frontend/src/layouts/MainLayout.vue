<template>
  <div class="main-layout">
    <el-container v-if="!isMobile" class="desktop-layout">
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
            active-text-color="#409eff"
          >
            <el-menu-item v-for="item in visiblePrimaryItems" :key="item.index" :index="item.index">
              <el-icon><component :is="item.icon" /></el-icon>
              <template #title>{{ item.title }}</template>
            </el-menu-item>

            <el-sub-menu v-for="section in visibleSections" :key="section.index" :index="section.index">
              <template #title>
                <el-icon><component :is="section.icon" /></el-icon>
                <span>{{ section.title }}</span>
              </template>
              <el-menu-item v-for="child in section.children" :key="child.index" :index="child.index">
                {{ child.title }}
              </el-menu-item>
            </el-sub-menu>

            <el-menu-item v-for="item in visibleReservedItems" :key="item.index" :index="item.index">
              <el-icon><component :is="item.icon" /></el-icon>
              <template #title>{{ item.title }}</template>
            </el-menu-item>
          </el-menu>
        </el-scrollbar>
      </el-aside>

      <el-container>
        <el-header class="header">
          <div class="header-left">
            <el-icon class="collapse-icon" @click="toggleCollapse">
              <Fold v-if="!isCollapse" />
              <Expand v-else />
            </el-icon>
            <div v-if="currentPageTitle" class="page-context">
              <strong class="page-context__title">{{ currentPageTitle }}</strong>
            </div>
          </div>

          <div class="header-right">
            <span :class="['env-badge', isPreviewEnv ? 'env-badge--preview' : 'env-badge--stable']">
              <span v-if="isPreviewEnv" class="env-dot"></span>
              {{ currentEnvLabel }}
            </span>

            <el-dropdown @command="handleCommand">
              <span class="user-info">
                <el-icon><User /></el-icon>
                <span>{{ authStore.userInfo?.full_name || '用户' }}</span>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item v-if="canSwitchEnvironment" command="switch-environment">
                    {{ switchButtonText }}
                  </el-dropdown-item>
                  <el-dropdown-item v-if="firstAdminPath" command="admin">
                    进入系统管理
                  </el-dropdown-item>
                  <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                  <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>

        <div v-if="authStore.passwordExpired" class="password-expired-banner">
          <el-alert
            type="warning"
            :closable="false"
            show-icon
            title="当前账号密码已过期，请尽快修改密码。"
          >
            <template #default>
              <el-button link type="warning" @click="openPasswordChange">
                立即修改密码
              </el-button>
            </template>
          </el-alert>
        </div>

        <el-main
          ref="mainContentRef"
          :class="['main-content', shouldCompactContentTitle ? 'main-content--page-title-compact' : '']"
        >
          <router-view />
        </el-main>
      </el-container>
    </el-container>

    <MobileLayout v-else>
      <router-view />
    </MobileLayout>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Expand, Fold, User } from '@element-plus/icons-vue'
import MobileLayout from './MobileLayout.vue'
import { useAuthStore } from '@/stores/auth'
import { useEnvironment } from '@/composables/useEnvironment'
import { useFeatureFlagStore } from '@/stores/featureFlag'
import { NAV_SECTIONS, PRIMARY_NAV_ITEMS, RESERVED_NAV_ITEMS } from '@/config/navigation'
import { canAccessRouteMeta, type RouteAccessMeta } from '@/utils/accessControl'
import { getEnvironmentLabel, isPreviewEnvironment } from '@/utils/environment'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const featureFlagStore = useFeatureFlagStore()
const { currentEnvironment, switchButtonText, switchEnvironment, syncEnvironmentState } = useEnvironment()

const isCollapse = ref(false)
const isMobile = ref(false)
const mainContentRef = ref<any>(null)

const activeMenu = computed(() => route.path)
const isPreviewEnv = computed(() => isPreviewEnvironment(currentEnvironment.value))
const currentEnvLabel = computed(() => getEnvironmentLabel(currentEnvironment.value))
const canSwitchEnvironment = computed(() => authStore.allowedEnvironments.length > 1)
const currentPageTitle = computed(() => String(route.meta.title || ''))
const shouldCompactContentTitle = computed(() => Boolean(currentPageTitle.value))
const routeAccessContext = computed(() => ({
  isAuthenticated: authStore.isAuthenticated,
  isInternal: authStore.isInternal,
  isSupplier: authStore.isSupplier,
  isPlatformAdmin: authStore.isPlatformAdmin,
  isFeatureEnabled: (featureKey: string) => featureFlagStore.isFeatureEnabled(featureKey),
  hasPermission: (modulePath: string, operation: 'create' | 'read' | 'update' | 'delete' | 'export') =>
    authStore.hasPermissionLocal(modulePath, operation),
}))

function canAccessPath(path: string) {
  const resolved = router.resolve(path)
  if (!resolved.matched.length) {
    return false
  }

  return canAccessRouteMeta(resolved.meta as RouteAccessMeta, routeAccessContext.value)
}

const visiblePrimaryItems = computed(() =>
  PRIMARY_NAV_ITEMS.filter((item) => canAccessPath(item.index))
)

const visibleSections = computed(() =>
  NAV_SECTIONS.map((section) => ({
    ...section,
    children: section.children.filter((child) => canAccessPath(child.index)),
  })).filter((section) => section.children.length > 0)
)

const visibleReservedItems = computed(() =>
  RESERVED_NAV_ITEMS.filter((item) => canAccessPath(item.index))
)

const firstAdminPath = computed(
  () => visibleSections.value.find((section) => section.index === 'admin')?.children[0]?.index ?? ''
)

function resolveMainContentElement() {
  return mainContentRef.value?.$el ?? mainContentRef.value ?? null
}

function clearCompactTitleState(root: ParentNode | null) {
  if (!root) {
    return
  }

  root.querySelectorAll('.page-stage').forEach((element) => {
    element.classList.remove('page-stage')
  })
  root.querySelectorAll('.page-title-compact-target').forEach((element) => {
    element.classList.remove('page-title-compact-target')
  })
  root.querySelectorAll('.page-title-compact-heading').forEach((element) => {
    element.classList.remove('page-title-compact-heading')
  })
  root.querySelectorAll('.page-title-compact-subcopy').forEach((element) => {
    element.classList.remove('page-title-compact-subcopy')
  })
}

function markCompactTitleCandidate(pageRoot: Element | null) {
  if (!pageRoot) {
    return
  }

  const directChildren = Array.from(pageRoot.children)
  const candidate = directChildren.find((child) => {
    if (!(child instanceof HTMLElement)) {
      return false
    }

    if (child.classList.contains('page-header')) {
      return true
    }

    return Boolean(child.querySelector(':scope > h1, :scope > h2, :scope > div > h1, :scope > div > h2'))
  })

  if (!(candidate instanceof HTMLElement)) {
    return
  }

  const heading =
    candidate.querySelector(':scope > h1, :scope > h2') ?? candidate.querySelector('h1, h2')
  if (heading instanceof HTMLElement) {
    candidate.classList.add('page-title-compact-target')
    heading.classList.add('page-title-compact-heading')
  }

  const subcopy = candidate.querySelector(':scope > p') ?? candidate.querySelector('p')
  if (subcopy instanceof HTMLElement) {
    subcopy.classList.add('page-title-compact-subcopy')
  }
}

async function syncCompactPageTitle() {
  await nextTick()
  const mainContent = resolveMainContentElement()
  clearCompactTitleState(mainContent)

  const pageRoot = mainContent?.querySelector(':scope > *')
  if (!(pageRoot instanceof Element)) {
    return
  }

  pageRoot.classList.add('page-stage')

  if (!shouldCompactContentTitle.value) {
    return
  }

  markCompactTitleCandidate(pageRoot)
}

function toggleCollapse() {
  isCollapse.value = !isCollapse.value
}

function updateIsMobile() {
  isMobile.value = window.innerWidth < 768
}

function handleCommand(command: string) {
  if (command === 'logout') {
    authStore.logout()
    router.push('/login')
    return
  }

  if (command === 'switch-environment') {
    switchEnvironment()
    return
  }

  if (command === 'admin') {
    router.push(firstAdminPath.value || '/workbench')
    return
  }

  router.push('/workbench')
}

function openPasswordChange() {
  router.push({
    path: '/workbench',
    query: {
      ...route.query,
      settings: 'password',
    },
  })
}

onMounted(async () => {
  updateIsMobile()
  window.addEventListener('resize', updateIsMobile)
  syncEnvironmentState()

  if (authStore.isAuthenticated) {
    await Promise.all([
      featureFlagStore.loadFeatureFlags(),
      authStore.loadPermissionTree(),
    ])
  }

  await syncCompactPageTitle()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateIsMobile)
})

watch(
  () => route.fullPath,
  async () => {
    await syncCompactPageTitle()
  }
)
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
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: #304156;
  color: #fff;
  transition: width 0.3s;
}

.sidebar :deep(.el-scrollbar) {
  flex: 1;
}

.sidebar :deep(.el-menu) {
  border-right: none;
}

.sidebar :deep(.el-sub-menu__title) {
  color: #bfcbd9 !important;
}

.sidebar :deep(.el-sub-menu__title:hover) {
  background-color: #263445 !important;
}

.sidebar :deep(.el-menu--inline) {
  background-color: #1f2d3d !important;
}

.sidebar :deep(.el-menu--inline .el-menu-item) {
  min-width: auto;
  padding-left: 50px !important;
  background-color: #1f2d3d !important;
  color: #bfcbd9 !important;
}

.sidebar :deep(.el-menu--inline .el-menu-item:hover) {
  background-color: #001528 !important;
}

.sidebar :deep(.el-menu--inline .el-menu-item.is-active) {
  color: #409eff !important;
}

.logo {
  display: flex;
  height: 60px;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  background-color: #2b3a4a;
  color: #fff;
  font-size: 20px;
  font-weight: 700;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e6e6e6;
  background-color: #fff;
  padding: 0 20px;
}

.password-expired-banner {
  padding: 12px 20px 0;
}

.password-expired-banner :deep(.el-alert) {
  border-radius: 12px;
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left {
  min-width: 0;
}

.collapse-icon {
  cursor: pointer;
  font-size: 20px;
  flex-shrink: 0;
}

.page-context {
  display: flex;
  min-width: 0;
  align-items: center;
}

.page-context__title {
  color: #1f2a37;
  font-size: 18px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.env-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: 999px;
  padding: 4px 12px;
  font-size: 12px;
  font-weight: 600;
  line-height: 1;
}

.env-badge--stable {
  border: 1px solid #b3d8ff;
  background-color: #ecf5ff;
  color: #409eff;
}

.env-badge--preview {
  border: 1px solid #f5dab1;
  background-color: #fdf6ec;
  color: #e6a23c;
}

.env-dot {
  display: inline-block;
  height: 6px;
  width: 6px;
  border-radius: 50%;
  background-color: #e6a23c;
  animation: env-dot-blink 1.2s ease-in-out infinite;
}

@keyframes env-dot-blink {
  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.2;
  }
}

.user-info {
  display: flex;
  cursor: pointer;
  align-items: center;
  gap: 8px;
}

.main-content {
  background-color: #f3f6fb;
  padding: 14px 16px 18px;
}

@media (max-width: 992px) {
  .page-context__title {
    font-size: 16px;
  }
}

@media (max-width: 768px) {
  .main-content {
    padding: 10px 12px 14px;
  }
}
</style>
