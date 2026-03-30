import { computed } from 'vue'

const PREVIEW_PREFIX = 'preview.'
const ENV_STORAGE_KEY = 'current_environment'

function isLocalHost(hostname: string) {
  return hostname === 'localhost' || hostname.startsWith('127.0.0.1')
}

function detectEnvironment(): 'stable' | 'preview' {
  const hostname = window.location.hostname

  if (hostname.includes('preview')) {
    return 'preview'
  }

  if (isLocalHost(hostname)) {
    return localStorage.getItem(ENV_STORAGE_KEY) === 'preview' ? 'preview' : 'stable'
  }

  return 'stable'
}

/**
 * Shared environment state for login, desktop and mobile layouts.
 *
 * Product rule:
 * - Stable and preview each have their own entry domain.
 * - The UI still exposes an explicit switch button.
 * - On server domains, switching jumps between domains.
 * - In local development, switching falls back to local state.
 */
export function useEnvironment() {
  const currentEnvironment = computed<'stable' | 'preview'>(() => detectEnvironment())
  const isPreview = computed(() => currentEnvironment.value === 'preview')

  const environmentName = computed(() => {
    return isPreview.value ? '预览版' : '正式版'
  })

  const switchButtonText = computed(() => {
    return isPreview.value ? '切换到正式版' : '切换到预览版'
  })

  const environmentBadgeClass = computed(() => {
    return isPreview.value ? 'environment-badge-preview' : 'environment-badge-stable'
  })

  const syncEnvironmentState = () => {
    localStorage.setItem(ENV_STORAGE_KEY, currentEnvironment.value)
  }

  const switchEnvironment = () => {
    const targetEnvironment: 'stable' | 'preview' = isPreview.value ? 'stable' : 'preview'
    const currentUrl = new URL(window.location.href)
    const hostname = currentUrl.hostname

    localStorage.setItem(ENV_STORAGE_KEY, targetEnvironment)

    if (isLocalHost(hostname)) {
      window.location.reload()
      return
    }

    currentUrl.hostname = isPreview.value
      ? hostname.replace(/^preview\./, '')
      : `${PREVIEW_PREFIX}${hostname}`

    window.location.href = currentUrl.toString()
  }

  return {
    currentEnvironment,
    isPreview,
    environmentName,
    switchButtonText,
    switchEnvironment,
    environmentBadgeClass,
    syncEnvironmentState
  }
}
