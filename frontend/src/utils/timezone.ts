import { systemSettingsApi } from '../api'

let cachedTimezone: string | null = null
let loadingTimezone: Promise<void> | null = null

export async function getTimezone(): Promise<string> {
  if (cachedTimezone) return cachedTimezone
  
  if (!loadingTimezone) {
    loadingTimezone = (async () => {
      try {
        const response = await systemSettingsApi.getPublicSystemSetting()
        cachedTimezone = response.data?.timezone || 'Asia/Shanghai'
      } catch {
        cachedTimezone = 'Asia/Shanghai'
      }
    })()
  }
  
  await loadingTimezone
  return cachedTimezone || 'Asia/Shanghai'
}

export function formatTimeWithTimezone(
  timeStr: string,
  options?: Intl.DateTimeFormatOptions
): Promise<string> {
  return getTimezone().then((tz) => {
    if (!timeStr) return '-'
    
    const date = new Date(timeStr)
    if (isNaN(date.getTime())) return '-'
    
    const defaultOptions: Intl.DateTimeFormatOptions = {
      timeZone: tz,
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }
    
    return date.toLocaleString('zh-CN', { ...defaultOptions, ...options })
  })
}

export function formatTimeWithTimezoneSync(
  timeStr: string,
  timezone: string = 'Asia/Shanghai',
  options?: Intl.DateTimeFormatOptions
): string {
  if (!timeStr) return '-'
  
  const date = new Date(timeStr)
  if (isNaN(date.getTime())) return '-'
  
  const defaultOptions: Intl.DateTimeFormatOptions = {
    timeZone: timezone,
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }
  
  return date.toLocaleString('zh-CN', { ...defaultOptions, ...options })
}
