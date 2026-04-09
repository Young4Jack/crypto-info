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
  // 更新账户信息（需要鉴权）
  updateAccount: (data: AccountUpdatePayload) => {
    return put<AccountUpdateResponse>('/api/auth/account', data)
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

// 更新账户请求载荷
export interface AccountUpdatePayload {
  username: string
  email?: string
  current_password?: string
  new_password?: string
  confirm_new_password?: string
}

// 更新账户响应结构
export interface AccountUpdateResponse {
  success: boolean
  message: string
  user: {
    id: number
    username: string
    email: string
  }
}

export interface WatchlistItem {
  id: number
  crypto_id: number
  crypto_symbol: string
  crypto_name: string
  notes: string
  created_at: string
  current_price: number
  sort_order: number
  is_public: boolean
}

export interface WatchlistCreatePayload {
  crypto_symbol: string
  notes?: string
  is_public?: boolean
}

export const watchlistApi = {
  getAllWatchlist: () => {
    return get('/api/watchlist/all')
  },
  getPublicWatchlist: () => {
    return get('/api/watchlist/public')
  },
  getList: () => {
    return get<WatchlistItem[]>('/api/watchlist/')
  },
  create: (data: WatchlistCreatePayload) => {
    return post<WatchlistItem>('/api/watchlist/', data)
  },
  update: (watchlistId: number, data: Partial<WatchlistCreatePayload>) => {
    return put<WatchlistItem>(`/api/watchlist/${watchlistId}`, data)
  },
  delete: (watchlistId: number) => {
    return del(`/api/watchlist/${watchlistId}`)
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
  getPublic: () => {
    return get('/api/system-settings/public')
  },
  getFull: () => {
    return get<SystemSettings>('/api/system-settings/')
  },
  save: (data: SystemSettingsPayload) => {
    return post<SystemSettings>('/api/system-settings/', data)
  },
  update: (data: SystemSettingsPayload) => {
    return put<SystemSettings>('/api/system-settings/', data)
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
export interface NotificationChannelPayload {
  name: string
  api_url: string
  auth_token?: string
  is_default?: boolean
  default_group?: string
  groups?: string[]
}

export const notificationChannelsApi = {
  getList: () => {
    return get<NotificationChannel[]>('/api/settings/notification-channels/')
  },
  create: (data: NotificationChannelPayload) => {
    return post<NotificationChannel>('/api/settings/notification-channels/', data)
  },
  update: (channelName: string, data: Partial<NotificationChannelPayload>) => {
    return put<NotificationChannel>(`/api/settings/notification-channels/${channelName}`, data)
  },
  delete: (channelName: string) => {
    return del(`/api/settings/notification-channels/${channelName}`)
  },
  test: (channelName: string) => {
    return post(`/api/settings/notification-channels/${channelName}/test`)
  },
}

// ==================== 仪表盘 (Dashboard) ====================

// 资产配置项（dashboard summary 返回的 asset_allocation 数组元素）
export interface AssetAllocationItem {
  crypto_symbol: string
  crypto_name: string
  quantity: number
  buy_price: number
  current_price: number
  holding_value: number
  buy_value: number
  profit_loss: number
  profit_loss_percentage: number
  sort_order: number
  created_at: string
}

// 关注列表项（dashboard summary 返回的 watchlist 数组元素）
export interface DashboardWatchlistItem {
  id: number
  crypto_symbol: string
  crypto_name: string
  current_price: number
  sort_order: number
}

// 预警项（dashboard summary 返回的 alerts 数组元素）
export interface DashboardAlertItem {
  id: number
  crypto_symbol: string
  crypto_name: string
  alert_type: string
  threshold_price: number
  current_price: number
  is_active: boolean
  sort_order: number
}

// 仪表盘综合数据响应
export interface DashboardSummaryResponse {
  total_value: number
  total_profit_loss: number
  total_profit_loss_percentage: number
  active_alerts_count: number
  asset_allocation: AssetAllocationItem[]
  watchlist: DashboardWatchlistItem[]
  alerts: DashboardAlertItem[]
  latest_news: any[]
  summary: {
    total_assets: number
    total_cryptocurrencies: number
  }
}

export const dashboardApi = {
  // 获取仪表盘综合数据（需要鉴权）
  getSummary: () => {
    return get<DashboardSummaryResponse>('/api/dashboard/summary')
  },
}

// ==================== 资产管理 (Assets) ====================

// 资产项响应结构
export interface AssetItem {
  id: number
  crypto_id: number
  crypto_symbol: string
  crypto_name: string
  buy_price: number
  quantity: number
  notes: string
  total_value: number
  current_price: number
  sort_order: number
  created_at: string
}

// 创建资产请求载荷
export interface AssetCreatePayload {
  crypto_symbol: string
  buy_price: number
  quantity: number
  notes?: string
}

// 更新资产请求载荷
export interface AssetUpdatePayload {
  buy_price?: number
  quantity?: number
  notes?: string
}

export const assetsApi = {
  // 获取资产列表（需要鉴权）
  getList: () => {
    return get<AssetItem[]>('/api/assets/')
  },
  // 获取单个资产（需要鉴权）
  getOne: (assetId: number) => {
    return get<AssetItem>(`/api/assets/${assetId}`)
  },
  // 创建资产（需要鉴权）
  create: (data: AssetCreatePayload) => {
    return post<AssetItem>('/api/assets/', data)
  },
  // 更新资产（需要鉴权）
  update: (assetId: number, data: AssetUpdatePayload) => {
    return put<AssetItem>(`/api/assets/${assetId}`, data)
  },
  // 删除资产（需要鉴权）
  delete: (assetId: number) => {
    return del(`/api/assets/${assetId}`)
  },
}

export interface PriceSearchResult {
  symbol: string
  name: string
  display_name: string
  price: number
  source: string
}

export const priceSearchApi = {
  search: (symbol: string) => {
    return get<PriceSearchResult>('/api/price-search/', { symbol })
  },
}

export interface ApiSettings {
  primary_api_url: string
  backup_api_url: string
  api_key: string
  api_secret: string
}

export const apiSettingsApi = {
  get: () => {
    return get<ApiSettings>('/api/api-settings/')
  },
  save: (data: ApiSettings) => {
    return post<ApiSettings>('/api/api-settings/', data)
  },
  testPrimary: () => {
    return post('/api/api-settings/test-primary')
  },
  testBackup: () => {
    return post('/api/api-settings/test-backup')
  },
}

export interface SystemSettings {
  refresh_interval: number
  enable_captcha: boolean
  site_title: string
  site_description: string
  base_url: string
  log_level: string
  enable_logging: boolean
  default_dark_mode: boolean
  api_shared_secret: string
  timezone: string
  backend_port: number
  frontend_port: number
  current_pricing_currency: string
  available_currencies: string[]
  exchange_rates: Record<string, number>
  exchange_rates_date: string
}

export interface SystemSettingsPayload {
  refresh_interval?: number
  enable_captcha?: boolean
  site_title?: string
  site_description?: string
  base_url?: string
  log_level?: string
  enable_logging?: boolean
  default_dark_mode?: boolean
  api_shared_secret?: string
  timezone?: string
  current_pricing_currency?: string
  available_currencies?: string[]
}
