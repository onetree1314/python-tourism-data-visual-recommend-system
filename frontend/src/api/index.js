import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  timeout: 30000
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    // 只有当token存在且格式正确时才添加Authorization头
    if (token && token.trim() !== '') {
      try {
        // 简单验证token格式（JWT通常有三部分，用.分隔）
        if (token.split('.').length === 3) {
          config.headers.Authorization = `Bearer ${token}`
        }
      } catch (e) {
        // token格式错误，不添加Authorization头
        console.warn('Token格式错误，跳过Authorization头')
      }
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    // 422错误通常是验证错误，不应该跳转到登录页
    if (error.response?.status === 401) {
      // 只在非登录页面时才跳转
      if (!window.location.pathname.includes('/login')) {
        localStorage.removeItem('token')
        window.location.href = '/login'
      }
    } else if (error.response?.status === 403) {
      // 权限不足
      console.error('权限不足')
    } else if (error.response?.status === 422) {
      // 422错误，通常是JWT token格式问题（如Subject must be a string）
      // 对于optional=True的路由，清除无效token并允许继续访问
      const token = localStorage.getItem('token')
      if (token) {
        // 检查是否是token相关错误
        const errorMsg = error.response?.data?.msg || error.response?.data?.message || ''
        if (errorMsg.includes('Subject') || errorMsg.includes('token') || errorMsg.includes('JWT')) {
          console.warn('检测到无效token，已清除:', errorMsg)
          localStorage.removeItem('token')
          // 对于可选认证的路由，清除token后重试请求（不带token）
          const url = error.config?.url || ''
          if (url.includes('/attractions/') && !url.includes('/favorite')) {
            // 这是景点详情页面，不需要token，清除token后重试
            // 返回一个特殊的错误标记，让调用方知道可以重试
            error.retryWithoutToken = true
          }
        }
      }
      console.error('请求验证失败:', error.response?.data)
    }
    return Promise.reject(error)
  }
)

// 认证相关
export const authAPI = {
  login: (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),
  getUserInfo: () => api.get('/auth/info'),
  logout: () => api.post('/auth/logout')
}

// 景点相关
export const attractionAPI = {
  getList: (params) => api.get('/attractions/list', { params }),
  getDetail: (id) => api.get(`/attractions/${id}`),
  getCities: () => api.get('/attractions/cities'),
  addFavorite: (data) => api.post('/attractions/favorite', data),
  removeFavorite: (id) => api.delete(`/attractions/favorite/${id}`),
  getFavorites: (params) => api.get('/attractions/favorites', { params }),
  getHistory: (params) => api.get('/attractions/history', { params })
}

// 推荐相关
export const recommendationAPI = {
  getIntelligent: (data) => api.post('/recommendation/intelligent', data),
  getSimilar: (id) => api.get(`/recommendation/similar/${id}`),
  getHot: (params) => api.get('/recommendation/hot', { params }),
  getTravelPlan: (data) => api.post('/recommendation/travel-plan', data),
  chat: (data) => api.post('/recommendation/chat', data)
}

// 分析相关
export const analyticsAPI = {
  getScoreDistribution: () => api.get('/analytics/score-distribution'),
  getCityAnalysis: () => api.get('/analytics/city-analysis'),
  getPriceSalesAnalysis: () => api.get('/analytics/price-sales-analysis'),
  getTagAnalysis: () => api.get('/analytics/tag-analysis'),
  getOverview: () => api.get('/analytics/overview')
}

// 管理员相关
export const adminAPI = {
  getUsers: (params) => api.get('/admin/users', { params }),
  updateUser: (id, data) => api.put(`/admin/users/${id}`, data),
  deleteUser: (id) => api.delete(`/admin/users/${id}`),
  getAttractions: (params) => api.get('/admin/attractions', { params }),
  deleteAttraction: (id) => api.delete(`/admin/attractions/${id}`),
  getSpiderTasks: (params) => api.get('/admin/spider-tasks', { params }),
  getLogs: (params) => api.get('/admin/logs', { params }),
  getStatistics: () => api.get('/admin/statistics'),
  getProvinceStatistics: () => api.get('/admin/province-statistics')
}

export default api
