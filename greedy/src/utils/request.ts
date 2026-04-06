import { apiBase } from './config'

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

  const token = uni.getStorageSync('token')
  const authHeader = token ? { Authorization: `Bearer ${token}` } : {}

  return new Promise((resolve, reject) => {
    uni.request({
      url: fullUrl,
      data,
      method,
      header: {
        'Content-Type': 'application/json',
        ...authHeader,
        ...header,
      },
      timeout: 10000,
      success: (res) => {
        if (res.statusCode === 401) {
          uni.removeStorageSync('token')
          uni.removeStorageSync('user')
          uni.reLaunch({ url: '/pages/login/login' })
          uni.showToast({ title: '登录已过期，请重新登录', icon: 'none' })
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
          const errorMsg = (res.data as any)?.detail || '请求失败'
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

export function get<T = any>(url: string, params?: Record<string, any>): Promise<ApiResponse<T>> {
  const query = params ? '?' + new URLSearchParams(params).toString() : ''
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
