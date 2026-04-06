import { get } from '../utils/request'

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
