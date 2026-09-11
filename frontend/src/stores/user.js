import { defineStore } from 'pinia'
import { authAPI } from '../api'

export const useUserStore = defineStore('user', {
  state: () => {
    const token = localStorage.getItem('token') || ''
    const userInfoStr = localStorage.getItem('userInfo')
    let userInfo = null
    try {
      if (userInfoStr) {
        userInfo = JSON.parse(userInfoStr)
      }
    } catch (e) {
      console.error('解析userInfo失败:', e)
    }
    return {
      userInfo,
      token
    }
  },
  
  getters: {
    isLoggedIn: (state) => !!state.token && !!state.userInfo,
    isAdmin: (state) => state.userInfo?.role === 'admin'
  },
  
  actions: {
    async login(credentials) {
      try {
        const res = await authAPI.login(credentials)
        if (res.code === 200) {
          this.token = res.data.access_token
          this.userInfo = res.data.user
          localStorage.setItem('token', res.data.access_token)
          localStorage.setItem('userInfo', JSON.stringify(res.data.user))
          return true
        }
        return false
      } catch (error) {
        console.error('Login error:', error)
        return false
      }
    },
    
    async register(data) {
      try {
        const res = await authAPI.register(data)
        return res.code === 200
      } catch (error) {
        console.error('Register error:', error)
        return false
      }
    },
    
    async getUserInfo() {
      if (!this.token) return
      try {
        const res = await authAPI.getUserInfo()
        if (res.code === 200) {
          this.userInfo = res.data
          localStorage.setItem('userInfo', JSON.stringify(res.data))
        }
      } catch (error) {
        console.error('Get user info error:', error)
        // Token可能过期或无效，清除登录状态
        this.token = ''
        this.userInfo = null
        localStorage.removeItem('token')
        localStorage.removeItem('userInfo')
      }
    },
    
    async logout() {
      try {
        if (this.token) {
          await authAPI.logout()
        }
      } catch (e) {
        console.error('Logout error:', e)
      } finally {
        this.token = ''
        this.userInfo = null
        localStorage.removeItem('token')
        localStorage.removeItem('userInfo')
      }
    }
  }
})
