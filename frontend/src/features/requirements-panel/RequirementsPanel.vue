<template>
  <div class="page">
    <div class="shell">
      <section v-if="!isAuthenticated" class="card login-layout">
        <div class="intro">
          <span class="eyebrow">Independent Requirements Panel</span>
          <h1>{{ catalog.metadata.title }}</h1>
          <p>
            这是部署在 QMS 子路径下的独立需求面板。它使用独立账号，不复用 QMS 主系统用户。
            管理员账号可以在线调整状态，查阅账号仅用于浏览和汇报。
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
          <div class="hero-copy">
            <span class="eyebrow">QMS Requirements Dashboard</span>
            <h1>{{ catalog.metadata.title }}</h1>
            <p>
              页面改成“概览 + 明细”双视图后，先用紧凑摘要定位重点模块，再进入明细模式维护状态。
              这样能保留汇报价值，同时避免把相同需求项在多个区块里重复铺开。
            </p>
            <div class="meta-row">
              <span class="pill">当前账号：{{ panelUser?.full_name }}</span>
              <span class="pill">账号角色：{{ canUpdate ? '管理员' : '查阅账号' }}</span>
              <span class="pill">版本：{{ catalog.metadata.version }}</span>
            </div>

            <div class="overview-strip">
              <article v-for="metric in headlineMetrics" :key="metric.label" class="metric-card">
                <span>{{ metric.label }}</span>
                <strong>{{ metric.value }}</strong>
                <small>{{ metric.note }}</small>
              </article>
            </div>
          </div>

          <div class="hero-side">
            <div class="hero-panel">
              <div class="panel-head">
                <div>
                  <h3>操作区</h3>
                  <p>刷新状态、导出快照或返回主系统。</p>
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
            </div>

            <div class="hero-panel">
              <div class="panel-head">
                <div>
                  <h3>当前焦点</h3>
                  <p>{{ attentionItems.length }} 条仍需优先关注的需求。</p>
                </div>
              </div>
              <div v-if="attentionItems.length > 0" class="panel-list">
                <article v-for="item in attentionItems.slice(0, 4)" :key="item.id" class="panel-item">
                  <div class="stack">
                    <strong>{{ item.title }}</strong>
                    <span>{{ item.moduleName }}</span>
                  </div>
                  <span class="status-pill" :class="`status-pill-${item.status}`">{{ statusText[item.status] }}</span>
                </article>
              </div>
              <p v-else class="empty-copy">当前筛选结果已无待推进项。</p>
            </div>
          </div>
        </section>

        <section class="card controls">
          <div class="section-head section-head-tight">
            <div>
              <h2>筛选与定位</h2>
              <p>保留统一筛选入口，概览和明细共用同一组条件，避免来回重复查找。</p>
            </div>
            <span class="pill">{{ filteredItems.length }} / {{ allItems.length }} 条需求</span>
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
            <div class="toolbar-group">
              <button class="ghost" type="button" @click="resetFilters">重置筛选</button>
              <span v-if="hasActiveFilters" class="pill subtle-pill">{{ activeFiltersCount }} 个筛选生效</span>
            </div>
            <div class="toolbar-group legend-group">
              <span v-for="legend in catalog.metadata.statusLegend" :key="legend.key" class="pill legend-pill">
                <span class="legend-dot" :class="`status-${legend.key}`"></span>
                {{ legend.label }}
              </span>
            </div>
          </div>
        </section>

        <section class="workspace">
          <div class="section-head workspace-head">
            <div>
              <h2>{{ activeView === 'overview' ? '总览模式' : '明细模式' }}</h2>
              <p>
                {{ activeView === 'overview'
                  ? '将模块进度、优先级和待推进事项压缩到同一屏内，先看重点再下钻。'
                  : '聚焦单一列表做核对和状态维护，避免与概览区重复占用页面长度。'
                }}
              </p>
            </div>

            <div class="view-switch" role="tablist" aria-label="需求面板视图切换">
              <button
                class="view-tab"
                :class="{ active: activeView === 'overview' }"
                type="button"
                @click="activeView = 'overview'"
              >
                总览
              </button>
              <button
                class="view-tab"
                :class="{ active: activeView === 'details' }"
                type="button"
                @click="activeView = 'details'"
              >
                明细
              </button>
            </div>
          </div>

          <template v-if="activeView === 'overview'">
            <div class="workspace-grid">
              <section class="card module-board">
                <div class="board-head">
                  <div>
                    <h3>模块摘要</h3>
                    <p>每个模块只保留进度、关键计数和少量焦点需求，避免完整列表重复铺陈。</p>
                  </div>
                  <span class="pill">{{ moduleSummaries.length }} 个命中模块</span>
                </div>

                <div v-if="moduleSummaries.length > 0" class="module-list">
                  <article v-for="module in moduleSummaries" :key="module.id" class="module-row">
                    <div class="module-header">
                      <div>
                        <div class="title-row">
                          <h3>{{ module.name }}</h3>
                          <span class="priority" :class="`priority-${module.overallPriority}`">
                            {{ priorityText[module.overallPriority] }}
                          </span>
                        </div>
                        <p>{{ module.summary }}</p>
                      </div>

                      <div class="module-progress">
                        <strong>{{ module.stats.progress }}%</strong>
                        <span>{{ module.stats.verified }}/{{ module.items.length }} 已验证</span>
                      </div>
                    </div>

                    <div class="track">
                      <div class="bar" :style="{ width: `${module.stats.progress}%` }"></div>
                    </div>

                    <div class="module-bottom">
                      <div class="mini-stats">
                        <span>开发中 {{ module.stats.doing }}</span>
                        <span>待验证 {{ module.stats.devDone }}</span>
                        <span>待开发 {{ module.stats.todo }}</span>
                      </div>

                      <div v-if="module.focusItems.length > 0" class="focus-badges">
                        <div v-for="item in module.focusItems" :key="item.id" class="focus-chip">
                          <strong>{{ item.title }}</strong>
                          <span>{{ statusText[item.status] }}</span>
                        </div>
                      </div>
                    </div>
                  </article>
                </div>

                <p v-else class="empty-copy board-empty">当前筛选条件下没有匹配的模块。</p>
              </section>

              <aside class="sidebar">
                <article class="card focus-card">
                  <div class="board-head">
                    <div>
                      <h3>优先级摘要</h3>
                      <p>优先级泳道压缩为计数卡，保留汇报信息但不再单独占满版面。</p>
                    </div>
                  </div>

                  <div class="priority-summary">
                    <div v-for="lane in prioritySummary" :key="lane.key" class="priority-block">
                      <div class="priority-line">
                        <span class="priority" :class="`priority-${lane.key}`">{{ lane.title }}</span>
                        <strong>{{ lane.items.length }}</strong>
                      </div>
                      <p>{{ lane.description }}</p>
                      <small>未完成 {{ lane.pendingCount }} 项</small>
                    </div>
                  </div>
                </article>

                <article class="card focus-card">
                  <div class="board-head">
                    <div>
                      <h3>状态分布</h3>
                      <p>直接看到筛选结果的状态构成，便于快速判断推进压力。</p>
                    </div>
                  </div>

                  <div class="status-summary">
                    <div v-for="status in statusSummary" :key="status.key" class="status-count">
                      <span class="legend-dot" :class="`status-${status.key}`"></span>
                      <div class="stack">
                        <strong>{{ status.count }}</strong>
                        <span>{{ status.label }}</span>
                      </div>
                    </div>
                  </div>
                </article>

                <article class="card focus-card">
                  <div class="board-head">
                    <div>
                      <h3>待推进清单</h3>
                      <p>从所有筛选结果中只挑最需要动作的条目，替代原来的大块重复列表。</p>
                    </div>
                  </div>

                  <div v-if="attentionItems.length > 0" class="panel-list">
                    <article v-for="item in attentionItems" :key="item.id" class="panel-item">
                      <div class="stack">
                        <strong>{{ item.title }}</strong>
                        <span>{{ item.moduleName }} · {{ item.phase }}</span>
                      </div>
                      <span class="priority" :class="`priority-${item.priority}`">{{ priorityText[item.priority] }}</span>
                    </article>
                  </div>
                  <p v-else class="empty-copy">当前无需额外推进项。</p>
                </article>
              </aside>
            </div>
          </template>

          <section v-else class="card detail-board">
            <div class="detail-toolbar">
              <span class="pill">共 {{ filteredItems.length }} 条需求</span>
              <span class="pill subtle-pill">当前视图只保留可操作明细，避免重复展示</span>
              <span v-if="canUpdate" class="pill subtle-pill">管理员可直接更新状态</span>
            </div>

            <div class="table-shell">
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
                  <tr v-if="filteredItems.length === 0">
                    <td colspan="7" class="table-empty-cell">
                      <p class="empty-copy">当前筛选条件下没有匹配的需求项。</p>
                    </td>
                  </tr>
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

type WorkspaceView = 'overview' | 'details'

const priorityRank: Record<RequirementPriority, number> = {
  high: 0,
  medium: 1,
  low: 2
}

const statusRank: Record<RequirementStatus, number> = {
  doing: 0,
  'dev-done': 1,
  todo: 2,
  reserved: 3,
  verified: 4
}

const router = useRouter()

const panelUser = ref<RequirementPanelUser | null>(null)
const activeView = ref<WorkspaceView>('overview')
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

function compareItems(a: DisplayRequirementItem, b: DisplayRequirementItem) {
  const priorityDelta = priorityRank[a.priority] - priorityRank[b.priority]
  if (priorityDelta !== 0) return priorityDelta

  const statusDelta = statusRank[a.status] - statusRank[b.status]
  if (statusDelta !== 0) return statusDelta

  const moduleDelta = a.moduleName.localeCompare(b.moduleName, 'zh-Hans-CN')
  if (moduleDelta !== 0) return moduleDelta

  return a.title.localeCompare(b.title, 'zh-Hans-CN')
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
      const items = filteredItems.value
        .filter((item) => item.moduleId === module.id)
        .sort(compareItems)
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

const moduleSummaries = computed(() =>
  [...filteredModules.value]
    .map((module) => ({
      ...module,
      focusItems: module.items
        .filter((item) => item.status !== 'verified' && item.status !== 'reserved')
        .slice(0, 3)
    }))
    .sort((a, b) => {
      const priorityDelta = priorityRank[a.overallPriority] - priorityRank[b.overallPriority]
      if (priorityDelta !== 0) return priorityDelta
      return a.stats.progress - b.stats.progress
    })
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

const prioritySummary = computed(() =>
  priorityLanes.value.map((lane) => ({
    ...lane,
    pendingCount: lane.items.filter((item) => item.status !== 'verified' && item.status !== 'reserved').length
  }))
)

const verifiedCount = computed(() => allItems.value.filter((item) => item.status === 'verified').length)
const inProgressCount = computed(() =>
  allItems.value.filter((item) => item.status === 'doing' || item.status === 'dev-done').length
)
const highPriorityCount = computed(() => allItems.value.filter((item) => item.priority === 'high').length)

const headlineMetrics = computed(() => [
  {
    label: '功能模块',
    value: catalog.modules.length,
    note: '用摘要卡片代替原来的独立统计区'
  },
  {
    label: '需求条目',
    value: allItems.value.length,
    note: '汇总所有模块需求'
  },
  {
    label: '已验证完成',
    value: verifiedCount.value,
    note: '主线进度一眼可见'
  },
  {
    label: '推进中',
    value: inProgressCount.value,
    note: `${highPriorityCount.value} 条高优先级需求`
  }
])

const statusSummary = computed(() =>
  catalog.metadata.statusLegend.map((legend) => ({
    ...legend,
    count: filteredItems.value.filter((item) => item.status === legend.key).length
  }))
)

const attentionItems = computed(() =>
  [...filteredItems.value]
    .filter((item) => item.status !== 'verified' && item.status !== 'reserved')
    .sort(compareItems)
    .slice(0, 6)
)

const activeFiltersCount = computed(
  () => [filters.keyword, filters.priority, filters.scope, filters.status, filters.moduleId].filter(Boolean).length
)

const hasActiveFilters = computed(() => activeFiltersCount.value > 0)

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
  activeView.value = 'overview'
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
  --surface: rgba(255, 255, 255, 0.94);
  --surface-strong: rgba(247, 250, 255, 0.98);
  --border: rgba(43, 72, 124, 0.12);
  --text: #172235;
  --muted: #60708b;
  --accent: #2a6bcf;
  min-height: 100vh;
  padding: 20px 16px 48px;
  background:
    radial-gradient(circle at top left, rgba(102, 153, 255, 0.22), transparent 34%),
    radial-gradient(circle at 90% 10%, rgba(22, 163, 74, 0.14), transparent 28%),
    linear-gradient(135deg, #f4f7fb 0%, #eaf1fb 45%, #dfe7f6 100%);
}

.shell {
  width: min(1440px, 100%);
  margin: 0 auto;
}

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  box-shadow: 0 24px 60px rgba(39, 67, 108, 0.12);
  backdrop-filter: blur(18px);
}

.login-layout,
.hero {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(320px, 0.95fr);
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
  color: var(--accent);
  font-size: 13px;
  font-weight: 700;
}

h1 {
  margin: 18px 0 12px;
  font-size: clamp(30px, 4vw, 44px);
  line-height: 1.08;
  color: var(--text);
}

h2,
h3,
p {
  margin: 0;
}

p {
  color: var(--muted);
  line-height: 1.8;
}

.meta-row,
.toolbar,
.hero-actions {
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
  background: rgba(255, 255, 255, 0.84);
  color: var(--muted);
  font-size: 13px;
}

.subtle-pill {
  background: rgba(235, 241, 252, 0.9);
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
  color: var(--muted);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

input,
select,
.ghost,
.primary,
.view-tab {
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
  color: var(--text);
}

.actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.primary,
.ghost,
.view-tab {
  padding: 12px 16px;
  font-weight: 700;
  cursor: pointer;
  transition:
    transform 0.18s ease,
    box-shadow 0.18s ease,
    border-color 0.18s ease;
}

.primary {
  border: none;
  background: linear-gradient(135deg, #2a6bcf, #2563eb);
  color: #fff;
}

.ghost,
.view-tab {
  border: 1px solid rgba(43, 72, 124, 0.14);
  background: #fff;
  color: var(--text);
}

.primary:hover,
.ghost:hover,
.view-tab:hover {
  transform: translateY(-1px);
  box-shadow: 0 16px 30px rgba(39, 67, 108, 0.12);
}

button:disabled {
  cursor: not-allowed;
  opacity: 0.72;
  transform: none;
  box-shadow: none;
}

.danger {
  color: #be123c;
}

.hero-copy {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.overview-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.metric-card,
.hero-panel {
  padding: 18px;
  border-radius: 22px;
  background: rgba(247, 250, 255, 0.98);
  border: 1px solid rgba(43, 72, 124, 0.08);
}

.metric-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.metric-card span,
.metric-card small {
  color: var(--muted);
}

.metric-card strong {
  font-size: 30px;
  color: var(--text);
}

.hero-side {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel-head,
.section-head,
.board-head,
.module-header,
.priority-line,
.panel-item,
.title-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.panel-head {
  align-items: flex-start;
}

.hero-actions {
  margin-top: 16px;
}

.panel-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 14px;
}

.panel-item {
  align-items: center;
  padding: 12px 14px;
  border-radius: 18px;
  background: rgba(248, 250, 252, 0.94);
  border: 1px solid rgba(43, 72, 124, 0.08);
}

.controls {
  margin-top: 22px;
  padding: 22px;
  border-radius: 24px;
}

.section-head {
  align-items: flex-end;
  margin: 34px 0 14px;
}

.section-head-tight,
.workspace-head,
.board-head {
  margin-top: 0;
}

.workspace-head {
  margin-bottom: 18px;
}

.filters {
  display: grid;
  grid-template-columns: 1.5fr repeat(4, minmax(120px, 1fr));
  gap: 14px;
  margin-top: 18px;
}

.field-search {
  min-width: 0;
}

.toolbar {
  margin-top: 16px;
  justify-content: space-between;
  align-items: center;
}

.toolbar-group {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.legend-group {
  justify-content: flex-end;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex: 0 0 auto;
}

.status-todo {
  background: #94a3b8;
}

.status-doing {
  background: #2563eb;
}

.status-dev-done {
  background: #7c3aed;
}

.status-verified {
  background: #16a34a;
}

.status-reserved {
  background: #64748b;
}

.workspace {
  margin-top: 30px;
}

.view-switch {
  display: inline-flex;
  gap: 8px;
  padding: 6px;
  border-radius: 18px;
  background: rgba(230, 238, 249, 0.9);
}

.view-tab {
  min-width: 92px;
  border-color: transparent;
  background: transparent;
  box-shadow: none;
}

.view-tab.active {
  background: #fff;
  color: var(--accent);
  border-color: rgba(42, 107, 207, 0.14);
  box-shadow: 0 12px 24px rgba(39, 67, 108, 0.08);
}

.workspace-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(320px, 0.9fr);
  gap: 22px;
}

.module-board,
.focus-card,
.detail-board {
  padding: 22px;
  border-radius: 24px;
}

.module-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 18px;
}

.module-row {
  padding: 18px;
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(249, 251, 255, 0.98), rgba(242, 246, 253, 0.92));
  border: 1px solid rgba(43, 72, 124, 0.08);
}

.title-row {
  justify-content: flex-start;
  align-items: center;
  flex-wrap: wrap;
}

.module-progress {
  min-width: 112px;
  text-align: right;
}

.module-progress strong {
  display: block;
  font-size: 28px;
  color: var(--text);
}

.module-progress span {
  color: var(--muted);
  font-size: 13px;
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

.module-bottom {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-top: 14px;
}

.mini-stats {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  color: var(--muted);
  font-size: 13px;
}

.focus-badges {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.focus-chip {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 140px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(43, 72, 124, 0.08);
}

.focus-chip strong,
.panel-item strong,
.stack strong {
  color: var(--text);
}

.focus-chip span,
.stack span,
.empty-copy,
.updated-by {
  color: var(--muted);
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.priority-summary,
.status-summary {
  display: grid;
  gap: 12px;
  margin-top: 16px;
}

.priority-block,
.status-count {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border-radius: 18px;
  background: rgba(248, 250, 252, 0.9);
  border: 1px solid rgba(43, 72, 124, 0.08);
}

.priority-block {
  flex-direction: column;
  align-items: stretch;
}

.priority-line strong {
  font-size: 24px;
  color: var(--text);
}

.priority-block small {
  color: var(--muted);
}

.priority,
.status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.priority-high {
  background: #ffe2e8;
  color: #e11d48;
}

.priority-medium {
  background: #ffeedf;
  color: #ea580c;
}

.priority-low {
  background: #dbeafe;
  color: #2563eb;
}

.status-pill-todo {
  background: #f1f5f9;
  color: #475569;
}

.status-pill-doing {
  background: #dbeafe;
  color: #1d4ed8;
}

.status-pill-dev-done {
  background: #ede9fe;
  color: #6d28d9;
}

.status-pill-verified {
  background: #dcfce7;
  color: #15803d;
}

.status-pill-reserved {
  background: #e2e8f0;
  color: #475569;
}

.detail-toolbar {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.table-shell {
  overflow: auto;
  border-radius: 22px;
  border: 1px solid rgba(43, 72, 124, 0.08);
}

.table {
  width: 100%;
  min-width: 1180px;
  border-collapse: collapse;
  background: rgba(255, 255, 255, 0.86);
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
  background: rgba(244, 248, 255, 0.98);
  color: #24324b;
  font-size: 13px;
  z-index: 1;
}

.table-empty-cell {
  padding: 36px 18px;
  text-align: center;
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

.board-empty {
  padding: 28px 0 6px;
}

@media (max-width: 1180px) {
  .overview-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .workspace-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 1024px) {
  .login-layout,
  .hero {
    grid-template-columns: 1fr;
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

  .module-bottom {
    flex-direction: column;
  }

  .focus-badges {
    justify-content: flex-start;
  }
}

@media (max-width: 768px) {
  .page {
    padding: 12px 12px 32px;
  }

  .login-layout,
  .hero,
  .controls,
  .module-board,
  .focus-card,
  .detail-board,
  .login-card {
    padding: 18px;
    border-radius: 20px;
  }

  .overview-strip,
  .filters {
    grid-template-columns: 1fr;
  }

  .section-head,
  .module-header,
  .panel-item,
  .priority-line {
    flex-direction: column;
    align-items: flex-start;
  }

  .toolbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .view-switch {
    width: 100%;
  }

  .view-tab {
    flex: 1 1 0;
    text-align: center;
  }

  .module-progress {
    min-width: 0;
    text-align: left;
  }
}
</style>
