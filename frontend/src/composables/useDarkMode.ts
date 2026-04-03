import { ref } from 'vue'
import { systemSettingsApi } from '../api'

const OVERRIDE_KEY = 'kline_dark_mode_override'
const defaultDarkMode = ref(false)
const isDarkMode = ref(false)
let initialized = false
let loadPromise: Promise<void> | null = null

export function useDarkMode() {
  if (!initialized) {
    initialized = true
    loadPromise = initDarkMode()
  }

  const toggleDarkMode = () => {
    isDarkMode.value = !isDarkMode.value
    localStorage.setItem(OVERRIDE_KEY, isDarkMode.value.toString())
  }

  return { isDarkMode, toggleDarkMode, loadPromise }
}

async function initDarkMode() {
  const override = localStorage.getItem(OVERRIDE_KEY)
  if (override !== null) {
    isDarkMode.value = override === 'true'
    return
  }

  try {
    const response = await systemSettingsApi.getPublicSystemSetting()
    defaultDarkMode.value = response.data?.default_dark_mode ?? false
    isDarkMode.value = defaultDarkMode.value
  } catch {
    isDarkMode.value = false
  }
}
