import { computed } from 'vue'

/**
 * 环境管理 Composable
 * 用于检测当前环境（预览版/正式版）并提供环境切换功能
 */
export function useEnvironment() {
  /**
   * 判断是否为预览环境
   * 通过检查域名中是否包含 'preview' 来判断
   */
  const isPreview = computed(() => {
    const hostname = window.location.hostname
    return hostname.includes('preview')
  })

  /**
   * 获取环境名称
   */
  const environmentName = computed(() => {
    return isPreview.value ? '预览版' : '正式版'
  })

  /**
   * 获取切换按钮文本
   */
  const switchButtonText = computed(() => {
    return isPreview.value ? '切换到正式版' : '切换到预览版'
  })

  /**
   * 切换环境
   * 保持当前路径和查询参数，仅切换域名
   * Token 通过 localStorage 自动共享
   */
  const switchEnvironment = () => {
    const currentUrl = new URL(window.location.href)
    const hostname = currentUrl.hostname
    
    let newHostname: string
    
    if (isPreview.value) {
      // 从预览环境切换到正式环境
      // 移除 'preview.' 前缀
      newHostname = hostname.replace(/^preview\./, '')
    } else {
      // 从正式环境切换到预览环境
      // 添加 'preview.' 前缀
      // 处理 localhost 的特殊情况
      if (hostname === 'localhost' || hostname.startsWith('127.0.0.1')) {
        // 开发环境，不进行切换
        console.warn('开发环境不支持环境切换')
        return
      }
      newHostname = `preview.${hostname}`
    }
    
    // 构建新的 URL
    currentUrl.hostname = newHostname
    
    // 跳转到新环境
    // 使用 location.href 而不是 location.replace，以便用户可以使用浏览器后退按钮
    window.location.href = currentUrl.toString()
  }

  /**
   * 获取环境标识的样式类
   */
  const environmentBadgeClass = computed(() => {
    return isPreview.value ? 'environment-badge-preview' : 'environment-badge-stable'
  })

  return {
    isPreview,
    environmentName,
    switchButtonText,
    switchEnvironment,
    environmentBadgeClass
  }
}
