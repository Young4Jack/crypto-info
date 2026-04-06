import { get, post, del, put } from '../utils/request'

// 认证模块接口
export const authApi = {
  // 获取验证码（无需鉴权）
  getCaptcha: () => {
    return get<CaptchaResponse>('/api/auth/captcha')
  },
  // 用户登录（无需鉴权）
  login: (data: LoginPayload) => {
    return post<LoginResponse>('/api/auth/login', data)
  },
  // 获取当前用户信息（需要鉴权）
  getMe: () => {
    return get<UserInfoResponse>('/api/auth/me')
  },
}

// 验证码响应结构
export interface CaptchaResponse {
  captcha_id: string
  captcha_image: string
  enabled: boolean
}

// 登录请求载荷
export interface LoginPayload {
  email: string
  password: string
  login_type: string
  captchaId?: string
  captchaAnswer?: number
}

// 登录响应结构
export interface LoginResponse {
  access_token: string
  token_type: string
}

// 用户信息响应结构
export interface UserInfoResponse {
  id: number
  username: string
  email: string
  is_active: boolean
  created_at: string
}

export const watchlistApi = {
  getAllWatchlist: () => {
    return get('/api/watchlist/all')
  },
  // 公开关注列表（无需鉴权，由 request.ts 统一拼接域名前缀）
  getPublicWatchlist: () => {
    return get('/api/watchlist/public')
  },
}

export const klinesApi = {
  getKlines: (symbol: string, interval: string = '1h', limit: number = 100) => {
    return get(`/api/klines/${symbol}`, { interval, limit })
  },
  getWatchlistKlines: (interval: string = '1h', limit: number = 50) => {
    return get('/api/klines/watchlist/all', { interval, limit })
  },
}

export const systemSettingsApi = {
  getPublicSystemSetting: () => {
    return get('/api/system-settings/public')
  },
}

// 预警管理接口
export const alertsApi = {
  // 获取预警列表（需要鉴权）
  getList: () => {
    return get<AlertItem[]>('/api/alerts/')
  },
  // 创建预警（需要鉴权）
  create: (data: AlertCreatePayload) => {
    return post<AlertItem>('/api/alerts/', data)
  },
  // 更新预警（需要鉴权）
  update: (alertId: number, data: AlertCreatePayload) => {
    return put<AlertItem>(`/api/alerts/${alertId}`, data)
  },
  // 删除预警（需要鉴权）
  delete: (alertId: number) => {
    return del(`/api/alerts/${alertId}`)
  },
}

// 预警项响应结构
export interface AlertItem {
  id: number
  crypto_id: number
  crypto_symbol: string
  crypto_name: string
  alert_type: string
  threshold_price: number
  current_price: number
  is_active: boolean
  created_at: string
  base_price: number
  threshold_value: number
  is_continuous: boolean
  interval_minutes: number
  max_notifications: number
  notified_count: number
  last_triggered_at: string | null
  triggered_at: string | null
  sort_order: number
}

// 创建预警请求载荷
export interface AlertCreatePayload {
  crypto_symbol: string
  alert_type: string
  threshold_price: number
  webhook_url?: string | null
  base_price?: number
  threshold_value?: number
  is_continuous?: boolean
  interval_minutes?: number
  max_notifications?: number
  notification_channel?: string
  notification_group?: string
}

// 通知渠道项
export interface NotificationChannel {
  name: string
  api_url: string
  auth_token: string
  is_default: boolean
  default_group: string
  groups: string[]
}

// 通知渠道管理接口
export const notificationChannelsApi = {
  // 获取所有通知渠道（需要鉴权）
  getList: () => {
    return get<NotificationChannel[]>('/api/settings/notification-channels/')
  },
}
