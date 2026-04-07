import { ref, watch } from 'vue'
import { get, put } from '@/utils/request'

export type ThemeMode = 'light' | 'dark' | 'system'

const STORAGE_KEY = 'app_theme_mode'

// 读取本地持久化的主题设置
function getSavedTheme(): ThemeMode {
  try {
    const saved = uni.getStorageSync(STORAGE_KEY) as ThemeMode
    if (['light', 'dark', 'system'].includes(saved)) return saved
  } catch { /* ignore */ }
  return 'system'
}

// 判断当前系统是否深色模式
function isSystemDark(): boolean {
  // #ifdef H5
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false
  // #endif
  // #ifndef H5
  try {
    const res = uni.getSystemInfoSync()
    return res.theme === 'dark'
  } catch {
    return false
  }
  // #endif
}

// 实际生效的暗黑状态（system 模式跟随系统）
function resolveDarkMode(mode: ThemeMode): boolean {
  return mode === 'dark' || (mode === 'system' && isSystemDark())
}

// 全局响应式状态
const themeMode = ref<ThemeMode>(getSavedTheme())
const isDarkMode = ref(resolveDarkMode(themeMode.value))

// 监听系统主题变化（仅 system 模式生效）
function setupSystemListener() {
  // #ifdef H5
  const mq = window.matchMedia('(prefers-color-scheme: dark)')
  const handler = (e: MediaQueryListEvent) => {
    if (themeMode.value === 'system') {
      isDarkMode.value = e.matches
      applyTheme(e.matches)
    }
  }
  mq.addEventListener?.('change', handler)
  // #endif
}

// 应用主题到页面
function applyTheme(dark: boolean) {
  const root: any = typeof document !== 'undefined' ? document.documentElement : null
  if (root) {
    if (dark) {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
  }

  // #ifndef H5
  try {
    uni.setNavigationBarColor({
      frontColor: dark ? '#ffffff' as const : '#000000' as const,
      backgroundColor: dark ? '#1a1a2e' : '#ffffff',
      animation: { duration: 200, timingFunc: 'easeIn' }
    })
  } catch { /* ignore */ }

  try {
    uni.setTabBarStyle({
      backgroundColor: dark ? '#1a1a2e' : '#ffffff',
      color: '#999999',
      selectedColor: '#409EFF',
      borderStyle: dark ? 'white' as const : 'black' as const
    })
  } catch { /* ignore */ }
  // #endif

  // #ifdef H5
  if (typeof document !== 'undefined') {
    document.documentElement.style.backgroundColor = dark ? '#0f1419' : '#f5f7fa'
    document.body.style.backgroundColor = dark ? '#0f1419' : '#f5f7fa'
  }
  // #endif
}

// 同步主题到后端配置
async function syncThemeToBackend(mode: ThemeMode, dark: boolean) {
  try {
    // 仅在用户选择明确模式（light/dark）时同步，system 模式不同步
    if (mode === 'system') return
    
    await put('/api/system-settings/', { default_dark_mode: dark })
    // console.log('[Theme] 同步到后端成功:', { mode, default_dark_mode: dark })
  } catch (e) {
    // console.warn('[Theme] 同步到后端失败:', e)
  }
}

// 初始化主题并从后端加载默认配置
async function initThemeFromBackend() {
  applyTheme(isDarkMode.value)
  
  try {
    const res = await get<{ default_dark_mode: boolean }>('/api/system-settings/public')
    const backendDark = res.data?.default_dark_mode ?? false
    
    // 如果本地未设置（首次使用），根据后端配置和系统主题决定
    const saved = uni.getStorageSync(STORAGE_KEY)
    if (!saved) {
      const systemDark = isSystemDark()
      if (backendDark && systemDark) {
        themeMode.value = 'system'
      } else if (backendDark) {
        themeMode.value = 'dark'
      } else if (systemDark) {
        themeMode.value = 'system'
      } else {
        themeMode.value = 'light'
      }
      isDarkMode.value = resolveDarkMode(themeMode.value)
      applyTheme(isDarkMode.value)
    }
    
    // console.log('[Theme] 后端配置加载完成, default_dark_mode:', backendDark)
  } catch (e) {
    // console.warn('[Theme] 获取后端配置失败，使用本地配置')
  }
}

// 初始化
initThemeFromBackend()
setupSystemListener()

// 监听 themeMode 变化，自动应用
watch(themeMode, (mode) => {
  const dark = resolveDarkMode(mode)
  isDarkMode.value = dark
  applyTheme(dark)
  // 持久化到本地
  try {
    uni.setStorageSync(STORAGE_KEY, mode)
  } catch { /* ignore */ }
  // 同步到后端
  syncThemeToBackend(mode, dark)
})

export function useTheme() {
  const setTheme = (mode: ThemeMode) => {
    themeMode.value = mode
  }

  const getThemeLabel = (mode: ThemeMode): string => {
    const labels: Record<ThemeMode, string> = {
      light: '浅色',
      dark: '深色',
      system: '跟随系统'
    }
    return labels[mode]
  }

  return {
    themeMode,
    isDarkMode,
    setTheme,
    getThemeLabel
  }
}
