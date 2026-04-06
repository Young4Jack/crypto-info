 import request from '../utils/request'

// 币种 API
export const cryptocurrenciesApi = {
  // 获取所有激活的币种
  getAll: () => {
    return request.get('/api/cryptocurrencies/')
  },
  
  // 获取所有币种（包括非激活）
  getAllWithInactive: () => {
    return request.get('/api/cryptocurrencies/all')
  },
  
  // 根据 ID 获取币种
  getById: (id: number) => {
    return request.get(`/api/cryptocurrencies/${id}`)
  },
  
  // 创建币种
  create: (data: { symbol: string; name: string; logo_url?: string }) => {
    return request.post('/api/cryptocurrencies/', null, { params: data })
  },
  
  // 更新币种
  update: (id: number, data: { symbol?: string; name?: string; logo_url?: string; is_active?: boolean }) => {
    return request.put(`/api/cryptocurrencies/${id}`, null, { params: data })
  },
  
  // 删除币种
  delete: (id: number) => {
    return request.delete(`/api/cryptocurrencies/${id}`)
  }
}

// 预警规则 API
export const alertsApi = {
  // 获取当前用户的所有预警规则
  getAll: () => {
    return request.get('/api/alerts/')
  },
  
  // 根据 ID 获取预警规则
  getById: (id: number) => {
    return request.get(`/api/alerts/${id}`)
  },
  
  // 创建预警规则
  create: (data: {
    crypto_symbol: string
    alert_type: 'above' | 'below' | 'amplitude' | 'percent_up' | 'percent_down'
    threshold_price: number
    is_continuous?: boolean
    max_notifications?: number
    interval_minutes?: number
    notification_channel?: string
    notification_group?: string
    base_price?: number
  }) => {
    return request.post('/api/alerts/', data)
  },
  
  // 更新预警规则
  update: (id: number, data: {
    alert_type?: 'above' | 'below' | 'amplitude' | 'percent_up' | 'percent_down'
    threshold_price?: number
    webhook_url?: string
    is_active?: boolean
    is_continuous?: boolean
    max_notifications?: number
    interval_minutes?: number
    notification_channel?: string
    notification_group?: string
    base_price?: number
  }) => {
    return request.put(`/api/alerts/${id}`, data)
  },
  
  // 删除预警规则
  delete: (id: number) => {
    return request.delete(`/api/alerts/${id}`)
  },
  
  // 批量更新排序
  updateSortOrder: (items: { id: number; sort_order: number }[]) => {
    return request.put('/api/alerts/sort-order', { items })
  },
  
  // 删除全部预警
  deleteAll: () => {
    return request.delete('/api/alerts/all')
  }
}

// 认证 API
export const authApi = {
  // 登录
  login: (email: string, password: string, captchaAnswer?: string, captchaId?: string) => {
    const data: any = { email, password }
    if (captchaAnswer !== undefined) {
      data.captchaAnswer = parseInt(captchaAnswer)
    }
    if (captchaId !== undefined) {
      data.captchaId = captchaId
    }
    return request.post('/api/auth/login', data)
  },
  
  // 获取验证码
  getCaptcha: () => {
    return request.get('/api/auth/captcha')
  },
  
  // 验证验证码
  verifyCaptcha: (captchaId: string, answer: number) => {
    return request.post('/api/auth/verify-captcha', { captcha_id: captchaId, answer })
  },
  
  // 获取当前用户信息
  getMe: () => {
    return request.get('/api/auth/me')
  },
  
  // 更新账户信息
  updateAccount: (data: {
    username?: string
    email?: string
    current_password: string
    new_password?: string
    confirm_new_password?: string
  }) => {
    return request.put('/api/auth/account', data)
  }
}

// 资产 API
export const assetsApi = {
  // 获取当前用户的所有资产
  getAll: () => {
    return request.get('/api/assets/')
  },
  
  // 根据 ID 获取资产
  getById: (id: number) => {
    return request.get(`/api/assets/${id}`)
  },
  
  // 创建资产
  create: (data: {
    crypto_symbol: string
    buy_price: number
    quantity: number
    notes?: string
  }) => {
    return request.post('/api/assets/', data)
  },
  
  // 更新资产
  update: (id: number, data: {
    buy_price?: number
    quantity?: number
    notes?: string
  }) => {
    return request.put(`/api/assets/${id}`, data)
  },
  
  // 删除资产
  delete: (id: number) => {
    return request.delete(`/api/assets/${id}`)
  },
  
  // 批量更新排序
  updateSortOrder: (items: { id: number; sort_order: number }[]) => {
    return request.put('/api/assets/sort-order', { items })
  },
  
  // 删除全部资产
  deleteAll: () => {
    return request.delete('/api/assets/all')
  }
}

// 仪表盘 API
export const dashboardApi = {
  // 获取仪表盘综合数据
  getSummary: () => {
    return request.get('/api/dashboard/summary')
  },
  
  // 获取资产配置占比数据（用于图表）
  getAllocation: () => {
    return request.get('/api/dashboard/allocation')
  }
}

// 系统设置 API
export const settingsApi = {
  // 获取通知设置
  getNotificationSetting: () => {
    return request.get('/api/settings/notification')
  },
  
  // 创建通知设置
  createNotificationSetting: (data: {
    api_url: string
    auth_token: string
    channel?: string
  }) => {
    return request.post('/api/settings/notification', data)
  },
  
  // 更新通知设置
  updateNotificationSetting: (data: {
    api_url?: string
    auth_token?: string
    channel?: string
  }) => {
    return request.put('/api/settings/notification', data)
  },
  
  // 删除通知设置
  deleteNotificationSetting: () => {
    return request.delete('/api/settings/notification')
  },
  
  // 测试通知设置
  testNotificationSetting: () => {
    return request.post('/api/settings/notification/test')
  }
}

// 通知渠道管理 API
export const notificationChannelsApi = {
  getAll: () => {
    return request.get('/api/settings/notification-channels/')
  },
  getDefault: () => {
    return request.get('/api/settings/notification-channels/default')
  },
  create: (data: {
    name: string
    api_url: string
    auth_token?: string
    is_default?: boolean
    default_group?: string
    groups?: string[]
  }) => {
    return request.post('/api/settings/notification-channels/', data)
  },
  update: (name: string, data: {
    name?: string
    api_url?: string
    auth_token?: string
    is_default?: boolean
    default_group?: string
    groups?: string[]
  }) => {
    return request.put(`/api/settings/notification-channels/${name}`, data)
  },
  delete: (name: string) => {
    return request.delete(`/api/settings/notification-channels/${name}`)
  },
  test: (name: string) => {
    return request.post(`/api/settings/notification-channels/${name}/test`)
  }
}

// API设置 API
export const apiSettingsApi = {
  // 获取API设置
  getApiSetting: () => {
    return request.get('/api/api-settings/')
  },
  
  // 创建API设置
  createApiSetting: (data: {
    primary_api_url: string
    backup_api_url?: string
    api_key?: string
    api_secret?: string
  }) => {
    return request.post('/api/api-settings/', data)
  },
  
  // 更新API设置
  updateApiSetting: (data: {
    primary_api_url?: string
    backup_api_url?: string
    api_key?: string
    api_secret?: string
  }) => {
    return request.put('/api/api-settings/', data)
  },
  
  // 删除API设置
  deleteApiSetting: () => {
    return request.delete('/api/api-settings/')
  },
  
  // 测试主API
  testPrimaryApi: () => {
    return request.post('/api/api-settings/test-primary')
  },
  
  // 测试备用API
  testBackupApi: () => {
    return request.post('/api/api-settings/test-backup')
  }
}

// 系统设置 API
export const systemSettingsApi = {
  // 获取系统设置
  getSystemSetting: () => {
    return request.get('/api/system-settings/')
  },
  
  // 获取公开的系统设置（无需认证）
  getPublicSystemSetting: () => {
    return request.get('/api/system-settings/public')
  },
  
  // 创建系统设置
  createSystemSetting: (data: {
    refresh_interval: number
    enable_captcha?: boolean
    site_title?: string
    site_description?: string
    base_url?: string
    log_level?: string
    enable_logging?: boolean
    default_dark_mode?: boolean
    api_shared_secret?: string
    timezone?: string
  }) => {
    return request.post('/api/system-settings/', data)
  },
  
  // 更新系统设置
  updateSystemSetting: (data: {
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
  }) => {
    return request.put('/api/system-settings/', data)
  },
  
  // 删除系统设置
  deleteSystemSetting: () => {
    return request.delete('/api/system-settings/')
  }
}

// 关注列表 API
export const watchlistApi = {
  // 获取当前用户的所有关注项
  getAll: () => {
    return request.get('/api/watchlist/')
  },
  
  // 获取公开的关注列表（无需认证）
  getPublic: () => {
    return request.get('/api/watchlist/public')
  },
  
  // 获取所有关注列表（包含is_public为false的，无需认证）
  getAllWatchlist: () => {
    return request.get('/api/watchlist/all')
  },
  
  // 创建新的关注项
  create: (data: {
    crypto_symbol: string
    notes?: string
    is_public?: boolean
  }) => {
    return request.post('/api/watchlist/', data)
  },
  
  // 更新关注项
  update: (id: number, data: {
    notes?: string
    is_public?: boolean
  }) => {
    return request.put(`/api/watchlist/${id}`, data)
  },
  
  // 删除关注项
  delete: (id: number) => {
    return request.delete(`/api/watchlist/${id}`)
  },
  
  // 批量更新排序
  updateSortOrder: (items: { id: number; sort_order: number }[]) => {
    return request.put('/api/watchlist/sort-order', { items })
  },
  
  // 删除全部关注
  deleteAll: () => {
    return request.delete('/api/watchlist/all')
  }
}

// K线数据 API
export const klinesApi = {
  // 获取指定交易对的K线数据
  getKlines: (symbol: string, interval: string = '1h', limit: number = 100) => {
    return request.get(`/api/klines/${symbol}`, { params: { interval, limit } })
  },
  
  // 获取关注列表中所有币种的K线数据
  getWatchlistKlines: (interval: string = '1h', limit: number = 50) => {
    return request.get('/api/klines/watchlist/all', { params: { interval, limit } })
  }
}
