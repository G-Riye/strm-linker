import axios from 'axios'
import { ElMessage, ElLoading } from 'element-plus'

// 创建 axios 实例
const api = axios.create({
  baseURL: import.meta.env.PROD ? '/api' : 'http://localhost:8000/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
let loadingInstance = null
api.interceptors.request.use(
  (config) => {
    // 对于某些请求显示加载动画
    if (config.showLoading !== false) {
      loadingInstance = ElLoading.service({
        text: '请求中...',
        background: 'rgba(0, 0, 0, 0.7)'
      })
    }
    
    // 可以在这里添加认证 token
    // config.headers.Authorization = `Bearer ${getToken()}`
    
    return config
  },
  (error) => {
    if (loadingInstance) {
      loadingInstance.close()
      loadingInstance = null
    }
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    if (loadingInstance) {
      loadingInstance.close()
      loadingInstance = null
    }
    return response.data
  },
  (error) => {
    if (loadingInstance) {
      loadingInstance.close()
      loadingInstance = null
    }
    
    // 统一错误处理
    const message = error.response?.data?.detail || error.message || '请求失败'
    const status = error.response?.status
    
    if (status === 404) {
      ElMessage.error('接口不存在')
    } else if (status === 500) {
      ElMessage.error('服务器内部错误')
    } else if (status >= 400 && status < 500) {
      ElMessage.error(message)
    } else {
      ElMessage.error('网络错误，请检查连接')
    }
    
    return Promise.reject(error)
  }
)

// 配置管理 API
export const configApi = {
  // 扫描目录
  scan: (data) => api.post('/config/scan', data),
  
  // 清理损坏的软链接
  cleanup: (directory, recursive = true) => 
    api.post('/config/cleanup', null, { params: { directory, recursive } }),
  
  // 监听服务管理
  getWatchStatus: () => api.get('/config/watch/status'),
  startWatcher: () => api.post('/config/watch/start'),
  stopWatcher: () => api.post('/config/watch/stop'),
  addWatchDirectory: (data) => api.post('/config/watch/add', data),
  removeWatchDirectory: (directory) => 
    api.delete('/config/watch/remove', { params: { directory } }),
  
  // 定时任务管理
  getScheduledTasks: () => api.get('/config/schedule/tasks'),
  addScheduledTask: (data) => api.post('/config/schedule/add', data),
  removeScheduledTask: (taskId) => api.delete(`/config/schedule/remove/${taskId}`),
  enableScheduledTask: (taskId) => api.post(`/config/schedule/enable/${taskId}`),
  disableScheduledTask: (taskId) => api.post(`/config/schedule/disable/${taskId}`),
  runTaskNow: (taskId) => api.post(`/config/schedule/run/${taskId}`),
  getSchedulerStatus: () => api.get('/config/schedule/status')
}

// 日志管理 API
export const logsApi = {
  // 获取日志
  getLogs: (params) => api.get('/logs/', { params }),
  
  // 获取日志级别
  getLogLevels: () => api.get('/logs/levels'),
  
  // 获取日志统计
  getLogStats: () => api.get('/logs/stats'),
  
  // 清理旧日志
  clearOldLogs: (days) => api.delete('/logs/clear', { params: { days } }),
  
  // 导出日志
  exportLogs: (params) => api.get('/logs/export', { 
    params,
    responseType: 'blob',
    showLoading: false
  }),
  
  // 测试日志
  testLogging: () => api.post('/logs/test')
}

// 目录浏览 API
export const browseApi = {
  // 浏览目录
  browse: (params) => api.get('/browse/', { params, showLoading: false }),
  
  // 搜索目录
  search: (params) => api.get('/browse/search', { params }),
  
  // 自动补全路径
  autocomplete: (params) => api.get('/browse/autocomplete', { params, showLoading: false }),
  
  // 获取系统驱动器
  getDrives: () => api.get('/browse/drives')
}

// 系统健康检查 API
export const systemApi = {
  // 健康检查
  getHealth: () => api.get('/health', { showLoading: false })
}

// 通用 API 方法
export const request = api

export default {
  configApi,
  logsApi,
  browseApi,
  systemApi,
  request
}
