import { ref, onUnmounted } from 'vue'
import { systemSettingsApi } from '@/api'

let cachedInterval = 5

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
  const timer = ref<ReturnType<typeof setInterval> | null>(null)
  const interval = ref(cachedInterval)

  const startAutoRefresh = async (callback: () => void | Promise<void>) => {
    interval.value = await getRefreshInterval()
    
    await callback()
    
    timer.value = setInterval(async () => {
      interval.value = await getRefreshInterval()
      await callback()
    }, interval.value * 1000)
  }

  const stopAutoRefresh = () => {
    if (timer.value) {
      clearInterval(timer.value)
      timer.value = null
    }
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
