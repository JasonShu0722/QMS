<template>
  <div class="page">
    <div class="shell">
      <section v-if="!isAuthenticated" class="card login-layout">
        <div class="intro">
          <span class="eyebrow">Independent Requirements Panel</span>
          <h1>{{ catalog.metadata.title }}</h1>
          <p>
            这是部署在 QMS 子路径下的独立需求面板。它使用单独账号，不复用 QMS 主系统用户。
            管理员账号可以在线调整状态，查阅账号只用于浏览和汇报。
          </p>
          <div class="meta-row">
            <span class="pill">访问路径：/requirements-panel</span>
            <span class="pill">账号体系：独立</span>
            <span class="pill">状态同步：在线维护</span>
          </div>
        </div>

        <form class="card login-card" @submit.prevent="handleLogin">
          <h2>登录需求面板</h2>
          <label class="field">
            <span>账号</span>
            <input v-model.trim="loginForm.username" type="text" autocomplete="username" />
          </label>
          <label class="field">
            <span>密码</span>
            <input v-model="loginForm.password" type="password" autocomplete="current-password" />
          </label>
          <div class="actions">
            <button class="primary" type="submit" :disabled="loginLoading">
              {{ loginLoading ? '登录中...' : '进入面板' }}
            </button>
            <button class="ghost" type="button" @click="goToQmsLogin">返回 QMS</button>
          </div>
        </form>
      </section>

      <template v-else>
        <section class="card hero">
          <div>
            <span class="eyebrow">QMS Requirements Dashboard</span>
            <h1>{{ catalog.metadata.title }}</h1>
            <p>
              用于持续整理、汇报和维护 QMS 项目的功能需求条目。模块状态在这里统一更新，
              验证完成后也可以直接在线调整为最新状态。
            </p>
            <div class="meta-row">
              <span class="pill">当前账号：{{ panelUser?.full_name }}</span>
              <span class="pill">账号角色：{{ canUpdate ? '管理员' : '查阅账号' }}</span>
              <span class="pill">版本：{{ catalog.metadata.version }}</span>
            </div>
          </div>
          <div class="hero-actions">
            <button class="ghost" type="button" @click="refreshStatuses" :disabled="loading">
              {{ loading ? '同步中...' : '刷新状态' }}
            </button>
            <button class="ghost" type="button" @click="exportSnapshot">导出快照</button>
            <button class="ghost" type="button" @click="goToQmsLogin">返回 QMS</button>
            <button class="ghost danger" type="button" @click="logoutFromPanel">退出面板账号</button>
          </div>
        </section>

        <section class="stats">
          <article class="card stat">
            <strong>{{ catalog.modules.length }}</strong>
            <span>功能模块</span>
          </article>
          <article class="card stat">
            <strong>{{ allItems.length }}</strong>
            <span>需求条目</span>
          </article>
          <article class="card stat">
            <strong>{{ verifiedCount }}</strong>
            <span>已验证完成</span>
          </article>
          <article class="card stat">
            <strong>{{ inProgressCount }}</strong>
            <span>开发推进中</span>
          </article>
          <article class="card stat">
            <strong>{{ highPriorityCount }}</strong>
            <span>高优先级条目</span>
          </article>
        </section>

        <section class="card controls">
          <div class="section-head">
            <div>
              <h2>筛选</h2>
              <p>按模块、优先级、范围和状态快速筛选当前关注内容。</p>
            </div>
          </div>

          <div class="filters">
            <label class="field field-search">
              <span>关键词</span>
              <input v-model.trim="filters.keyword" type="search" placeholder="搜索模块、功能、验收标准" />
            </label>
            <label class="field">
              <span>优先级</span>
              <select v-model="filters.priority">
                <option value="">全部</option>
                <option value="high">高</option>
                <option value="medium">中</option>
                <option value="low">低 / 预留</option>
              </select>
            </label>
            <label class="field">
              <span>需求范围</span>
              <select v-model="filters.scope">
                <option value="">全部</option>
                <option value="核心需求">核心需求</option>
                <option value="期望增强">期望增强</option>
                <option value="预留功能">预留功能</option>
              </select>
            </label>
            <label class="field">
              <span>开发状态</span>
              <select v-model="filters.status">
                <option value="">全部</option>
                <option v-for="legend in catalog.metadata.statusLegend" :key="legend.key" :value="legend.key">
                  {{ legend.label }}
                </option>
              </select>
            </label>
            <label class="field">
              <span>功能模块</span>
              <select v-model="filters.moduleId">
                <option value="">全部</option>
                <option v-for="module in catalog.modules" :key="module.id" :value="module.id">
                  {{ module.name }}
                </option>
              </select>
            </label>
          </div>

          <div class="toolbar">
            <button class="ghost" type="button" @click="resetFilters">重置筛选</button>
            <span v-for="legend in catalog.metadata.statusLegend" :key="legend.key" class="pill legend-pill">
              <span class="legend-dot" :class="`status-${legend.key}`"></span>
              {{ legend.label }}
            </span>
          </div>
        </section>

        <section>
          <div class="section-head">
            <div>
              <h2>按功能模块</h2>
              <p>用于查看各模块整体优先级、条目数量和验证进度。</p>
            </div>
            <span class="pill">{{ filteredModules.length }} 个模块命中筛选</span>
          </div>

          <div class="module-grid">
            <article v-for="module in filteredModules" :key="module.id" class="card module-card">
              <div class="module-top">
                <div>
                  <div class="title-row">
                    <h3>{{ module.name }}</h3>
                    <span class="priority" :class="`priority-${module.overallPriority}`">
                      {{ priorityText[module.overallPriority] }}
                    </span>
                  </div>
                  <p>{{ module.summary }}</p>
                </div>
                <div class="metric">{{ module.stats.verified }}/{{ module.items.length }}</div>
              </div>

              <div class="track">
                <div class="bar" :style="{ width: `${module.stats.progress}%` }"></div>
              </div>

              <div class="mini-stats">
                <span>开发中 {{ module.stats.doing }}</span>
                <span>待验证 {{ module.stats.devDone }}</span>
                <span>待开发 {{ module.stats.todo }}</span>
              </div>
            </article>
          </div>
        </section>

        <section>
          <div class="section-head">
            <div>
              <h2>按整体优先级</h2>
              <p>用于和公司汇报优先级保持一致，快速聚焦当前最关键的条目。</p>
            </div>
          </div>

          <div class="lane-grid">
            <article v-for="lane in priorityLanes" :key="lane.key" class="card lane">
              <header class="lane-header">
                <div>
                  <h3>{{ lane.title }}</h3>
                  <p>{{ lane.description }}</p>
                </div>
                <span class="pill">{{ lane.items.length }} 项</span>
              </header>

              <div class="lane-list">
                <div v-for="item in lane.items" :key="item.id" class="lane-item">
                  <div>
                    <strong>{{ item.title }}</strong>
                    <span>{{ item.moduleName }}</span>
                  </div>
                  <span class="status-pill" :class="`status-pill-${item.status}`">{{ statusText[item.status] }}</span>
                </div>
                <p v-if="lane.items.length === 0" class="empty-copy">当前筛选下暂无条目。</p>
              </div>
            </article>
          </div>
        </section>

        <section>
          <div class="section-head">
            <div>
              <h2>需求明细台账</h2>
              <p>管理员可以直接在这里更新开发状态，查阅账号保持只读。</p>
            </div>
            <span class="pill">{{ filteredItems.length }} 条明细</span>
          </div>

          <div class="card table-shell">
            <table class="table">
              <thead>
                <tr>
                  <th>功能模块</th>
                  <th>功能条目</th>
                  <th>优先级</th>
                  <th>范围</th>
                  <th>阶段</th>
                  <th>开发状态</th>
                  <th>验收标准</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in filteredItems" :key="item.id">
                  <td>
                    <div class="stack">
                      <strong>{{ item.moduleName }}</strong>
                      <span>{{ item.moduleSummary }}</span>
                    </div>
                  </td>
                  <td>
                    <div class="stack">
                      <strong>{{ item.title }}</strong>
                      <span>ID: {{ item.id }}</span>
                    </div>
                  </td>
                  <td>
                    <span class="priority" :class="`priority-${item.priority}`">{{ priorityText[item.priority] }}</span>
                  </td>
                  <td>{{ item.scope }}</td>
                  <td>{{ item.phase }}</td>
                  <td class="status-cell">
                    <select
                      v-if="canUpdate"
                      :value="item.status"
                      :disabled="savingItemId === item.id"
                      @change="handleStatusChange(item.id, ($event.target as HTMLSelectElement).value)"
                    >
                      <option v-for="legend in catalog.metadata.statusLegend" :key="legend.key" :value="legend.key">
                        {{ legend.label }}
                      </option>
                    </select>
                    <span v-else class="status-pill" :class="`status-pill-${item.status}`">{{ statusText[item.status] }}</span>
                    <small v-if="item.updatedByName" class="updated-by">最近更新：{{ item.updatedByName }}</small>
                  </td>
                  <td>{{ item.acceptance }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { requirementsPanelApi } from './api'
import { requirementsPanelCatalog as catalog } from './catalog'
import type {
  RequirementCatalogItem,
  RequirementPanelUser,
  RequirementPriority,
  RequirementStatus,
  RequirementStatusOverride
} from './types'
import {
  REQUIREMENTS_PANEL_AUTH_EXPIRED_EVENT,
  REQUIREMENTS_PANEL_TOKEN_KEY,
  clearRequirementsPanelSession,
  getStoredRequirementsPanelUser,
  saveRequirementsPanelSession
} from './request'

interface DisplayRequirementItem extends RequirementCatalogItem {
  moduleId: string
  moduleName: string
  moduleSummary: string
  updatedByName?: string | null
  updatedAt?: string | null
}

const router = useRouter()

const panelUser = ref<RequirementPanelUser | null>(null)
const loginLoading = ref(false)
const loading = ref(false)
const savingItemId = ref<string | null>(null)
const canUpdate = ref(false)
const overrides = ref<Record<string, RequirementStatusOverride>>({})

const loginForm = reactive({
  username: '',
  password: ''
})

const filters = reactive({
  keyword: '',
  priority: '',
  scope: '',
  status: '',
  moduleId: ''
})

const isAuthenticated = computed(() => !!panelUser.value)

const statusText: Record<RequirementStatus, string> = {
  todo: '待开发',
  doing: '开发中',
  'dev-done': '已开发待验证',
  verified: '已验证完成',
  reserved: '预留'
}

const priorityText: Record<RequirementPriority, string> = {
  high: '高',
  medium: '中',
  low: '低 / 预留'
}

const mergedModules = computed(() =>
  catalog.modules.map((module) => ({
    ...module,
    items: module.items.map((item) => {
      const override = overrides.value[item.id]
      return {
        ...item,
        status: override?.status ?? item.status,
        updatedByName: override?.updated_by_name ?? null,
        updatedAt: override?.updated_at ?? null
      }
    })
  }))
)

const allItems = computed<DisplayRequirementItem[]>(() =>
  mergedModules.value.flatMap((module) =>
    module.items.map((item) => ({
      ...item,
      moduleId: module.id,
      moduleName: module.name,
      moduleSummary: module.summary
    }))
  )
)

const filteredItems = computed(() => {
  const keyword = filters.keyword.trim().toLowerCase()

  return allItems.value.filter((item) => {
    const matchesKeyword =
      !keyword ||
      item.moduleName.toLowerCase().includes(keyword) ||
      item.title.toLowerCase().includes(keyword) ||
      item.acceptance.toLowerCase().includes(keyword)

    const matchesPriority = !filters.priority || item.priority === filters.priority
    const matchesScope = !filters.scope || item.scope === filters.scope
    const matchesStatus = !filters.status || item.status === filters.status
    const matchesModule = !filters.moduleId || item.moduleId === filters.moduleId

    return matchesKeyword && matchesPriority && matchesScope && matchesStatus && matchesModule
  })
})

const filteredModules = computed(() =>
  mergedModules.value
    .map((module) => {
      const items = filteredItems.value.filter((item) => item.moduleId === module.id)
      const verified = items.filter((item) => item.status === 'verified').length
      const doing = items.filter((item) => item.status === 'doing').length
      const devDone = items.filter((item) => item.status === 'dev-done').length
      const todo = items.filter((item) => item.status === 'todo').length

      return {
        ...module,
        items,
        stats: {
          verified,
          doing,
          devDone,
          todo,
          progress: items.length === 0 ? 0 : Math.round((verified / items.length) * 100)
        }
      }
    })
    .filter((module) => module.items.length > 0)
)

const priorityLanes = computed(() => [
  {
    key: 'high',
    title: '高优先级',
    description: '直接决定项目主线交付节奏和汇报关注点。',
    items: filteredItems.value.filter((item) => item.priority === 'high')
  },
  {
    key: 'medium',
    title: '中优先级',
    description: '支撑主线闭环和分析能力的关键补位。',
    items: filteredItems.value.filter((item) => item.priority === 'medium')
  },
  {
    key: 'low',
    title: '低优先级 / 预留',
    description: '面向后续迭代、扩展治理和长期建设。',
    items: filteredItems.value.filter((item) => item.priority === 'low')
  }
])

const verifiedCount = computed(() => allItems.value.filter((item) => item.status === 'verified').length)
const inProgressCount = computed(() =>
  allItems.value.filter((item) => item.status === 'doing' || item.status === 'dev-done').length
)
const highPriorityCount = computed(() => allItems.value.filter((item) => item.priority === 'high').length)

async function refreshStatuses() {
  if (!panelUser.value) return

  loading.value = true
  try {
    const response = await requirementsPanelApi.getStatuses()
    canUpdate.value = response.can_update
    overrides.value = response.items.reduce<Record<string, RequirementStatusOverride>>((acc, item) => {
      acc[item.item_id] = item
      return acc
    }, {})
  } finally {
    loading.value = false
  }
}

async function restoreSession() {
  const storedUser = getStoredRequirementsPanelUser()
  if (storedUser) {
    panelUser.value = storedUser
    canUpdate.value = storedUser.role === 'admin'
  }

  const token = localStorage.getItem(REQUIREMENTS_PANEL_TOKEN_KEY)
  if (!token) return

  try {
    const user = await requirementsPanelApi.getCurrentUser()
    panelUser.value = user
    canUpdate.value = user.role === 'admin'
    saveRequirementsPanelSession(token, user)
    await refreshStatuses()
  } catch {
    handleLogout(false)
  }
}

async function handleLogin() {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请先输入账号和密码')
    return
  }

  loginLoading.value = true
  try {
    const response = await requirementsPanelApi.login({
      username: loginForm.username,
      password: loginForm.password
    })
    saveRequirementsPanelSession(response.access_token, response.user)
    panelUser.value = response.user
    canUpdate.value = response.user.role === 'admin'
    loginForm.password = ''
    await refreshStatuses()
    ElMessage.success('需求面板登录成功')
  } finally {
    loginLoading.value = false
  }
}

async function handleStatusChange(itemId: string, nextStatus: string) {
  const status = nextStatus as RequirementStatus
  const current = overrides.value[itemId]?.status ?? allItems.value.find((item) => item.id === itemId)?.status
  if (!status || current === status) return

  savingItemId.value = itemId
  try {
    const updated = await requirementsPanelApi.updateStatus(itemId, { status })
    overrides.value = {
      ...overrides.value,
      [itemId]: updated
    }
    ElMessage.success('需求状态已更新')
  } finally {
    savingItemId.value = null
  }
}

function resetFilters() {
  filters.keyword = ''
  filters.priority = ''
  filters.scope = ''
  filters.status = ''
  filters.moduleId = ''
}

function exportSnapshot() {
  const snapshot = {
    exported_at: new Date().toISOString(),
    current_user: panelUser.value,
    items: allItems.value.map((item) => ({
      id: item.id,
      module: item.moduleName,
      title: item.title,
      priority: item.priority,
      scope: item.scope,
      phase: item.phase,
      status: item.status,
      updated_by_name: item.updatedByName ?? null,
      updated_at: item.updatedAt ?? null
    }))
  }

  const blob = new Blob([JSON.stringify(snapshot, null, 2)], { type: 'application/json;charset=utf-8' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `qms-requirements-snapshot-${new Date().toISOString().slice(0, 10)}.json`
  link.click()
  window.URL.revokeObjectURL(url)
}

function goToQmsLogin() {
  router.push('/login')
}

function handleLogout(showMessage = true) {
  clearRequirementsPanelSession()
  panelUser.value = null
  canUpdate.value = false
  overrides.value = {}
  loginForm.password = ''
  if (showMessage) {
    ElMessage.success('已退出需求面板账号')
  }
}

function logoutFromPanel() {
  handleLogout(true)
}

function handleAuthExpired() {
  handleLogout(false)
}

onMounted(() => {
  restoreSession()
  window.addEventListener(REQUIREMENTS_PANEL_AUTH_EXPIRED_EVENT, handleAuthExpired)
})

onBeforeUnmount(() => {
  window.removeEventListener(REQUIREMENTS_PANEL_AUTH_EXPIRED_EVENT, handleAuthExpired)
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  padding: 20px 16px 48px;
  background: linear-gradient(135deg, #f4f7fb 0%, #eaf1fb 45%, #dfe7f6 100%);
}

.shell {
  width: min(1440px, 100%);
  margin: 0 auto;
}

.card {
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(43, 72, 124, 0.12);
  box-shadow: 0 24px 60px rgba(39, 67, 108, 0.12);
  backdrop-filter: blur(18px);
}

.login-layout,
.hero {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 28px;
  border-radius: 28px;
}

.intro {
  max-width: 820px;
}

.eyebrow {
  display: inline-flex;
  padding: 8px 12px;
  border-radius: 999px;
  background: #dbe8ff;
  color: #2a6bcf;
  font-size: 13px;
  font-weight: 700;
}

h1 {
  margin: 18px 0 12px;
  font-size: clamp(30px, 4vw, 44px);
  line-height: 1.08;
  color: #172235;
}

h2, h3, p {
  margin: 0;
}

p {
  color: #60708b;
  line-height: 1.8;
}

.meta-row,
.toolbar,
.stats,
.module-grid,
.lane-grid {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.meta-row {
  margin-top: 18px;
}

.pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 999px;
  border: 1px solid rgba(43, 72, 124, 0.14);
  background: rgba(255, 255, 255, 0.8);
  color: #60708b;
  font-size: 13px;
}

.login-card {
  width: min(400px, 100%);
  padding: 24px;
  border-radius: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field span {
  font-size: 12px;
  font-weight: 700;
  color: #60708b;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

input,
select,
.ghost,
.primary {
  border-radius: 14px;
  font-size: 14px;
}

input,
select {
  width: 100%;
  box-sizing: border-box;
  padding: 12px 14px;
  border: 1px solid rgba(43, 72, 124, 0.14);
  background: #fff;
  color: #172235;
}

.actions,
.hero-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.primary,
.ghost {
  padding: 12px 16px;
  font-weight: 700;
  cursor: pointer;
}

.primary {
  border: none;
  background: linear-gradient(135deg, #2a6bcf, #2563eb);
  color: #fff;
}

.ghost {
  border: 1px solid rgba(43, 72, 124, 0.14);
  background: #fff;
  color: #172235;
}

.danger {
  color: #be123c;
}

.stats {
  margin-top: 22px;
}

.stat {
  min-width: 180px;
  padding: 20px;
  border-radius: 22px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stat strong {
  font-size: 34px;
  color: #172235;
}

.stat span {
  color: #60708b;
}

.controls {
  margin-top: 22px;
  padding: 22px;
  border-radius: 24px;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
  margin: 34px 0 14px;
}

.section-head:first-child {
  margin-top: 0;
}

.filters {
  display: grid;
  grid-template-columns: 1.6fr repeat(4, minmax(120px, 1fr));
  gap: 14px;
  margin-top: 18px;
}

.field-search {
  min-width: 0;
}

.toolbar {
  margin-top: 16px;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.status-todo { background: #94a3b8; }
.status-doing { background: #2563eb; }
.status-dev-done { background: #7c3aed; }
.status-verified { background: #16a34a; }
.status-reserved { background: #64748b; }

.module-grid,
.lane-grid {
  margin-top: 22px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
}

.module-card,
.lane {
  padding: 22px;
  border-radius: 24px;
}

.module-top,
.lane-header,
.lane-item,
.title-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.title-row {
  justify-content: flex-start;
  align-items: center;
  flex-wrap: wrap;
}

.metric {
  min-width: 72px;
  text-align: right;
  font-size: 24px;
  font-weight: 800;
  color: #172235;
}

.track {
  width: 100%;
  height: 10px;
  margin-top: 16px;
  border-radius: 999px;
  background: #e8eef8;
  overflow: hidden;
}

.bar {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #2a6bcf, #16a34a);
}

.mini-stats {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-top: 12px;
  color: #60708b;
  font-size: 13px;
}

.priority,
.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.priority-high { background: #ffe2e8; color: #e11d48; }
.priority-medium { background: #ffeedf; color: #ea580c; }
.priority-low { background: #dbeafe; color: #2563eb; }

.lane-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 16px;
}

.lane-item {
  padding: 14px;
  border-radius: 18px;
  background: rgba(248, 250, 252, 0.9);
  border: 1px solid rgba(43, 72, 124, 0.08);
}

.lane-item strong,
.stack strong {
  color: #172235;
}

.lane-item span,
.stack span,
.empty-copy,
.updated-by {
  color: #60708b;
}

.status-pill-todo { background: #f1f5f9; color: #475569; }
.status-pill-doing { background: #dbeafe; color: #1d4ed8; }
.status-pill-dev-done { background: #ede9fe; color: #6d28d9; }
.status-pill-verified { background: #dcfce7; color: #15803d; }
.status-pill-reserved { background: #e2e8f0; color: #475569; }

.table-shell {
  overflow: auto;
  border-radius: 24px;
}

.table {
  width: 100%;
  min-width: 1180px;
  border-collapse: collapse;
}

.table th,
.table td {
  padding: 16px 18px;
  border-bottom: 1px solid rgba(43, 72, 124, 0.1);
  text-align: left;
  vertical-align: top;
}

.table th {
  position: sticky;
  top: 0;
  background: rgba(244, 248, 255, 0.96);
  color: #24324b;
  font-size: 13px;
}

.stack {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.status-cell {
  min-width: 180px;
}

.updated-by {
  display: block;
  margin-top: 8px;
  font-size: 12px;
}

@media (max-width: 1024px) {
  .login-layout,
  .hero {
    flex-direction: column;
  }

  .login-card {
    width: 100%;
  }

  .filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .field-search {
    grid-column: 1 / -1;
  }
}

@media (max-width: 768px) {
  .page {
    padding: 12px 12px 32px;
  }

  .login-layout,
  .hero,
  .controls,
  .module-card,
  .lane,
  .stat {
    padding: 18px;
    border-radius: 20px;
  }

  .filters {
    grid-template-columns: 1fr;
  }

  .section-head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
