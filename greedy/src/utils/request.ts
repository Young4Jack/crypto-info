import { apiBase } from './config'

// 白名单：无需携带 Token 的公开接口路径（前缀匹配）
const WHITE_LIST = [
  '/api/auth/login',
  '/api/auth/captcha',
  '/api/auth/verify-captcha',
  '/api/watchlist/public',
  '/api/watchlist/all',
  '/api/klines',
  '/api/system-settings/public',
  '/health',
]

// 判断请求路径是否命中白名单（支持精确匹配或严格前缀匹配，避免 '/' 误伤所有路径）
function isInWhiteList(url: string): boolean {
  const cleanUrl = url.split('?')[0]
  return WHITE_LIST.some((path) => cleanUrl === path || cleanUrl.startsWith(path + '/'))
}

// 未登录态拦截：清除缓存并跳转登录页，携带 redirect 参数
function redirectToLogin() {
  uni.removeStorageSync('token')
  uni.removeStorageSync('user')
  // 获取当前页面路径，登录后返回
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const route = currentPage?.route ? `/${currentPage.route}` : ''
  const redirectUrl = route ? encodeURIComponent(route) : ''
  // 使用 navigateTo 保留页面栈，登录后 navigateBack 可返回
  uni.navigateTo({
    url: `/pages/login/login${redirectUrl ? `?redirect=${redirectUrl}` : ''}`,
    fail: () => { uni.reLaunch({ url: '/pages/login/login' }) }
  })
  uni.showToast({ title: '请先登录', icon: 'none' })
}

interface RequestOptions {
  url: string
  data?: Record<string, any>
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  header?: Record<string, string>
}

interface ApiResponse<T = any> {
  data: T
  statusCode: number
}

// 拼接完整 URL：相对路径自动补 apiBase 前缀，绝对路径保持不变
function resolveUrl(url: string): string {
  if (url.startsWith('http://') || url.startsWith('https://')) return url
  const base = apiBase.value.replace(/\/$/, '')
  const path = url.startsWith('/') ? url : `/${url}`
  return base ? `${base}${path}` : path
}

function request<T = any>(options: RequestOptions): Promise<ApiResponse<T>> {
  const { url, data, method = 'GET', header = {} } = options
  const fullUrl = resolveUrl(url)

  // 白名单接口不携带 Token，非白名单接口必须携带有效 Token
  let authHeader: Record<string, string> = {}
  if (!isInWhiteList(url)) {
    const rawToken = uni.getStorageSync('token')
    // 清理空白字符后校验：排除 null、undefined、空字符串、"undefined"、"null" 等无效值
    const token = typeof rawToken === 'string' ? rawToken.trim() : ''
    const isValidToken = token && token !== 'undefined' && token !== 'null'

    if (!isValidToken) {
      redirectToLogin()
      return Promise.reject(new Error('Unauthorized: no valid token'))
    }
    authHeader = { Authorization: `Bearer ${token}` }
  }

  const requestHeaders = {
    'Content-Type': 'application/json',
    ...authHeader,
    ...header,
  }

  return new Promise((resolve, reject) => {
    uni.request({
      url: fullUrl,
      data,
      method,
      header: requestHeaders,
      timeout: 10000,
      success: (res) => {
        if (res.statusCode === 401) {
          // 非白名单接口返回 401 说明 Token 已失效，清除并跳转
          if (!isInWhiteList(url)) {
            redirectToLogin()
          }
          reject(new Error('Unauthorized'))
          return
        }

        if (res.statusCode >= 200 && res.statusCode < 300) {
          let parsedData = res.data as T
          if (typeof res.data === 'string') {
            try {
              parsedData = JSON.parse(res.data) as T
            } catch {
              parsedData = res.data as T
            }
          }
          resolve({ data: parsedData, statusCode: res.statusCode })
        } else {
          const raw = (res.data as any)?.detail
          const errorMsg = typeof raw === 'string' ? raw : Array.isArray(raw) ? raw.map((e: any) => e?.msg).filter(Boolean).join('; ') : '请求失败'
          uni.showToast({ title: errorMsg, icon: 'none' })
          reject(new Error(errorMsg))
        }
      },
      fail: (err) => {
        uni.showToast({ title: '网络连接失败', icon: 'none' })
        reject(err)
      },
    })
  })
}

// App/小程序环境无 URLSearchParams，手动序列化查询参数
function serializeQuery(params: Record<string, any>): string {
  return Object.entries(params)
    .filter(([, v]) => v !== undefined && v !== null)
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
    .join('&')
}

export function get<T = any>(url: string, params?: Record<string, any>): Promise<ApiResponse<T>> {
  const query = params && Object.keys(params).length ? `?${serializeQuery(params)}` : ''
  return request<T>({ url: url + query, method: 'GET' })
}

export function post<T = any>(url: string, data?: Record<string, any>): Promise<ApiResponse<T>> {
  return request<T>({ url, data, method: 'POST' })
}

export function put<T = any>(url: string, data?: Record<string, any>): Promise<ApiResponse<T>> {
  return request<T>({ url, data, method: 'PUT' })
}

export function del<T = any>(url: string): Promise<ApiResponse<T>> {
  return request<T>({ url, method: 'DELETE' })
}
