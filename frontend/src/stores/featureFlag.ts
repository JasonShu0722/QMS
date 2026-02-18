import { defineStore } from 'pinia'
import { ref } from 'vue'

/**
 * 功能特性开关类型
 */
export interface FeatureFlag {
  key: string
  name: string
  description: string
  is_enabled: boolean
  scope: 'global' | 'whitelist'
  whitelist_user_ids?: number[]
  whitelist_supplier_ids?: number[]
}

/**
 * 功能特性开关 Store
 * 管理系统功能的可见性和可用性
 * 
 * 对应需求：2.12.3 功能特性开关
 */
export const useFeatureFlagStore = defineStore('featureFlag', () => {
  // State
  const features = ref<Record<string, FeatureFlag>>({})
  const loading = ref(false)

  /**
   * 检查功能是否启用
   * @param featureKey 功能键名
   * @returns 是否启用
   */
  function isFeatureEnabled(featureKey: string): boolean {
    const feature = features.value[featureKey]
    
    if (!feature) {
      // 功能不存在，默认不启用
      return false
    }

    if (!feature.is_enabled) {
      // 功能全局禁用
      return false
    }

    if (feature.scope === 'global') {
      // 全局启用
      return true
    }

    // 白名单模式：需要检查当前用户是否在白名单中
    // 这里简化处理，实际应该从 authStore 获取当前用户信息
    const userInfoStr = localStorage.getItem('user_info')
    if (!userInfoStr) {
      return false
    }

    try {
      const userInfo = JSON.parse(userInfoStr)
      
      // 检查用户ID白名单
      if (feature.whitelist_user_ids && feature.whitelist_user_ids.includes(userInfo.id)) {
        return true
      }

      // 检查供应商ID白名单
      if (userInfo.supplier_id && feature.whitelist_supplier_ids && 
          feature.whitelist_supplier_ids.includes(userInfo.supplier_id)) {
        return true
      }

      return false
    } catch (error) {
      console.error('Failed to parse user info:', error)
      return false
    }
  }

  /**
   * 从后端加载功能开关配置
   */
  async function loadFeatureFlags(): Promise<void> {
    loading.value = true
    
    try {
      // 动态导入避免循环依赖
      const { featureFlagApi } = await import('@/api/featureFlag')
      const response = await featureFlagApi.getMyFeatures()
      
      // 转换为 Map 结构便于查询
      features.value = response.reduce((acc: Record<string, FeatureFlag>, feature: FeatureFlag) => {
        acc[feature.key] = feature
        return acc
      }, {})
    } catch (error) {
      console.error('Failed to load feature flags:', error)
      // 加载失败时使用默认配置（所有预留功能默认禁用）
      features.value = {
        'instruments.management': {
          key: 'instruments.management',
          name: '仪器量具管理',
          description: '仪器量具全生命周期管理功能',
          is_enabled: false,
          scope: 'global'
        },
        'quality-cost.management': {
          key: 'quality-cost.management',
          name: '质量成本管理',
          description: '质量成本统计与分析功能',
          is_enabled: false,
          scope: 'global'
        }
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * 更新功能开关状态（管理员功能）
   * @param featureKey 功能键名
   * @param enabled 是否启用
   */
  async function updateFeatureFlag(featureKey: string, enabled: boolean): Promise<void> {
    try {
      const { featureFlagApi } = await import('@/api/featureFlag')
      await featureFlagApi.updateFeatureFlag(featureKey, { is_enabled: enabled })
      
      // 更新本地状态
      if (features.value[featureKey]) {
        features.value[featureKey].is_enabled = enabled
      }
    } catch (error) {
      console.error('Failed to update feature flag:', error)
      throw error
    }
  }

  return {
    // State
    features,
    loading,
    
    // Actions
    isFeatureEnabled,
    loadFeatureFlags,
    updateFeatureFlag
  }
})
