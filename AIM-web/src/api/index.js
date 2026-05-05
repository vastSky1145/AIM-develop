/**
 * API 服务配置
 */
import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
  // baseURL: 'http://localhost:8000/api',
  // baseURL: 'http://192.168.1.96:8000/api',
  baseURL: '/api',   // 相对路径，统一由 nginx 转发
  timeout: 900000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 从 localStorage 获取 token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
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
    if (error.response) {
      // 401 未授权，跳转到登录页
      if (error.response.status === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('userInfo')
        window.location.href = '/#/login'
      }
      return Promise.reject(error.response.data)
    }
    return Promise.reject(error)
  }
)

// 认证相关
export const authAPI = {
  // 登录
  login(data) {
    return api.post('/auth/login', data)
  },
  // 获取当前用户信息
  getUserInfo() {
    return api.get('/auth/me')
  },
  // 修改密码
  changePassword(data) {
    return api.post('/auth/change-password', data)
  }
}

// 论文相关
export const paperAPI = {
  // 获取论文列表
  getList() {
    return api.get('/papers/list')
  },
  // 获取论文详情
  getDetail(title) {
    return api.get(`/papers/get/${encodeURIComponent(title)}`)
  },
  // 上传PPT
  // 旧api，上传参数为file，现在改为json数据
  // uploadPPT(file) {
  //   const formData = new FormData()
  //   formData.append('file', file)
  //   return api.post('/papers/upload-ppt', formData, {
  //     headers: { 'Content-Type': 'multipart/form-data' }
  //   })
  uploadPPT(jsonData) {
    return api.post('/papers/upload-ppt', jsonData)
  },
  // Agent 解析：仅提交任务，不等解析完成
  uploadPDF(file) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/papers/upload-pdf', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000
    })
  },
  // 查询 Agent 解析任务状态
  getTaskStatus(taskId) {
    return api.get(`/papers/task/${taskId}`)
  },
  // 快速解析（字符串匹配，同步）
  uploadPDFFast(file) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/papers/upload-pdf-fast', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000
    })
  },
  // 创建论文
  create(data) {
    return api.post('/papers/create', data)
  },
  // 更新论文
  update(data) {
    return api.put('/papers/update', data)
  },
  // 删除论文
  delete(data) {
    return api.delete('/papers/delete', { data })
  }
}

// AI 辅助相关
export const aiAPI = {
  // 生成内容
  generate(data) {
    return api.post('/ai/generate', data)
  },
  // 修改内容
  modify(data) {
    return api.post('/ai/modify', data)
  },
  // 提交评分
  submitRating(data) {
    return api.post('/ai/rating', data)
  }
}

// 知识库相关
export const knowledgeAPI = {
  // 检索
  search(data) {
    return api.post('/knowledge/search', data)
  },
  // 上传PDF
  uploadPDF(file) {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/knowledge/upload-pdf', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000 // 5分钟超时
    })
  },
  // 获取来源列表
  getSources() {
    return api.get('/knowledge/sources')
  },
  // 删除知识
  delete(data) {
    return api.delete('/knowledge/delete', { data })
  },
  // 清空知识库
  clear() {
    return api.delete('/knowledge/clear')
  }
}

// Prompt 模板相关
export const promptAPI = {
  // 获取模板
  get(pptId) {
    return api.get(`/prompts/get/${pptId}`)
  },
  // 保存模板
  save(data) {
    return api.post('/prompts/save', data)
  }
}

// 用户Prompt管理相关
export const userPromptAPI = {
  // 收藏夹相关
  getFolders() {
    return api.get('/user-prompts/folders')
  },
  createFolder(data) {
    return api.post('/user-prompts/folders', data)
  },
  updateFolder(folderId, data) {
    return api.put(`/user-prompts/folders/${folderId}`, data)
  },
  deleteFolder(folderId) {
    return api.delete(`/user-prompts/folders/${folderId}`)
  },
  
  // Prompts相关
  getPromptsByFolder(folderId) {
    return api.get(`/user-prompts/list?folder_id=${folderId}`)
  },
  createPrompt(data) {
    return api.post('/user-prompts/create', data)
  },
  updatePrompt(promptId, data) {
    return api.put(`/user-prompts/update/${promptId}`, data)
  },
  deletePrompt(promptId) {
    return api.delete(`/user-prompts/delete/${promptId}`)
  },
  searchPrompts(keyword) {
    return api.get(`/user-prompts/search?keyword=${encodeURIComponent(keyword)}`)
  },
  
  // 版本控制
  getVersions(promptId) {
    return api.get(`/user-prompts/versions/${promptId}`)
  }
}

export default api

