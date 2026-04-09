import { ref, onUnmounted } from 'vue'
import { systemSettingsApi } from '@/api'

let cachedInterval = 5
let globalTimer: ReturnType<typeof setInterval> | null = null

async function getRefreshInterval(): Promise<number> {
  try {
    const res = await systemSettingsApi.getPublic()
    cachedInterval = res.data?.refresh_interval || 8
  } catch {
    // 使用缓存值或默认值
  }
  return cachedInterval
}

export function useAutoRefresh() {
  const interval = ref(cachedInterval)
  const isRunning = ref(false)

  const startAutoRefresh = async (callback: (isBackground?: boolean) => void | Promise<void>) => {
    if (isRunning.value) return
    
    interval.value = await getRefreshInterval()
    isRunning.value = true
    
    await callback(false)
    
    globalTimer = setInterval(async () => {
      interval.value = await getRefreshInterval()
      await callback(true)
    }, interval.value * 1000)
  }

  const stopAutoRefresh = () => {
    if (globalTimer) {
      clearInterval(globalTimer)
      globalTimer = null
    }
    isRunning.value = false
  }

  onUnmounted(() => {
    stopAutoRefresh()
  })

  return {
    startAutoRefresh,
    stopAutoRefresh,
    interval
  }
}
