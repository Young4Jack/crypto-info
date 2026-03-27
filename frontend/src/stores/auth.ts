import { defineStore } from 'pinia'
import { authApi } from '../api'

interface User {
  id: number
  username: string
  email: string
  is_active: boolean
  created_at: string
}

interface AuthState {
  token: string | null
  user: User | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    token: localStorage.getItem('token'),
    user: JSON.parse(localStorage.getItem('user') || 'null')
  }),

  actions: {
    async login(email: string, password: string, captchaAnswer?: string, captchaId?: string) {
      try {
        const response = await authApi.login(email, password, captchaAnswer, captchaId)
        const { access_token } = response.data
        
        this.token = access_token
        localStorage.setItem('token', access_token)
        
        // 获取用户信息
        await this.fetchUserInfo()
        
        return true
      } catch (error: any) {
        console.error('登录失败:', error)
        throw new Error(error.response?.data?.detail || '登录失败')
      }
    },

    async fetchUserInfo() {
      try {
        const response = await authApi.getMe()
        this.user = response.data
        localStorage.setItem('user', JSON.stringify(response.data))
      } catch (error) {
        console.error('获取用户信息失败:', error)
        this.logout()
      }
    },

    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },

    isAuthenticated() {
      return !!this.token
    }
  }
})