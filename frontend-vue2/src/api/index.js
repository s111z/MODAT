import axios from 'axios'
import mockService from '@/mock'

const API_BASE_URL = process.env.VUE_APP_API_URL || 'http://localhost:5000'

// 配置 axios 默认选项
axios.defaults.baseURL = API_BASE_URL
axios.defaults.timeout = 30000
axios.defaults.headers.post['Content-Type'] = 'application/json'

/**
 * API 客户端类
 */
class APIClient {
  constructor(baseUrl = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  // ========== 聊天相关接口 ==========

  /**
   * 普通聊天接口
   * @param {Object} message - 消息对象 { message: string, mode?: 'qa' | 'review' }
   * @returns {Promise<Object>} { response: string, steps: string[] }
   */
  async chat(message) {
    // Mock 模式
    if (mockService.isEnabled()) {
      if (message.mode === 'document-review') {
        return await mockService.sendDocumentReviewMessage(message.message)
      }
      return await mockService.sendQAMessage(message.message)
    }

    // 真实 API
    try {
      const response = await axios.post(`${this.baseUrl}/api/chat`, message)
      return response.data
    } catch (error) {
      throw new Error(`API请求失败: ${error.message}`)
    }
  }

  /**
   * 流式聊天接口
   * @param {Object} message - 消息对象
   * @param {Function} onData - 数据回调函数
   * @param {Function} onError - 错误回调函数
   * @param {Function} onComplete - 完成回调函数
   */
  async chatStream(message, onData, onError, onComplete) {
    // Mock 模式
    if (mockService.isEnabled()) {
      try {
        await mockService.sendQAMessageStream(
          message.message,
          onData,
          onData
        )
        if (onComplete) onComplete()
      } catch (error) {
        if (onError) onError(error)
      }
      return
    }

    // 真实 API
    try {
      const response = await fetch(`${this.baseUrl}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(message),
      })

      if (!response.ok) {
        throw new Error(`API请求失败: ${response.statusText}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) {
          if (onComplete) onComplete()
          break
        }

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data.trim()) {
              try {
                const event = JSON.parse(data)
                if (onData) onData(event)
              } catch (e) {
                console.error('解析流数据失败:', e)
              }
            }
          }
        }
      }
    } catch (error) {
      if (onError) onError(error)
      throw error
    }
  }

  /**
   * 文档审核接口
   * @param {Object} request - { filename: string, message: string, mode?: string }
   * @returns {Promise<Object>}
   */
  async review(request) {
    try {
      const response = await axios.post(`${this.baseUrl}/api/review`, request)
      return response.data
    } catch (error) {
      throw new Error(`文档审核请求失败: ${error.message}`)
    }
  }

  // ========== 文件上传接口 ==========

  /**
   * 上传文件用于审核
   * @param {File} file - 文件对象
   * @returns {Promise<Object>} { savefilename, size, status, message }
   */
  async uploadFile(file) {
    // Mock 模式
    if (mockService.isEnabled()) {
      return await mockService.uploadFile(file)
    }

    // 真实 API
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post(`${this.baseUrl}/api/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return response.data
    } catch (error) {
      const message = error.response?.data?.detail || error.message
      throw new Error(`文件上传失败: ${message}`)
    }
  }

  /**
   * 上传文件到知识库
   * @param {File} file - 文件对象
   * @param {Object} metadata - 元数据
   * @returns {Promise<Object>}
   */
  async uploadKnowledgeFile(file, metadata = {}) {
    // Mock 模式
    if (mockService.isEnabled()) {
      return await mockService.uploadDocument(file, metadata)
    }

    // 真实 API
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await axios.post(`${this.baseUrl}/api/knowledge_upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return response.data
    } catch (error) {
      const message = error.response?.data?.detail || error.message
      throw new Error(`知识库文件上传失败: ${message}`)
    }
  }

  // ========== 向量库管理接口 ==========

  /**
   * 添加文档到向量库
   * @param {Object} request - { filename: string, metadatas?: Object }
   * @returns {Promise<Object>}
   */
  async vectorDBAdd(request) {
    try {
      const response = await axios.post(`${this.baseUrl}/api/vectordb/add`, request)
      return response.data
    } catch (error) {
      const message = error.response?.data?.detail || error.message
      throw new Error(`添加文档失败: ${message}`)
    }
  }

  /**
   * 搜索向量库
   * @param {Object} request - { query: string, top_k?: number, filter_meta?: Object }
   * @returns {Promise<Object>}
   */
  async vectorDBSearch(request) {
    // Mock 模式
    if (mockService.isEnabled()) {
      return await mockService.search(request.query)
    }

    // 真实 API
    try {
      const response = await axios.post(`${this.baseUrl}/api/vectordb/search`, request)
      return response.data
    } catch (error) {
      const message = error.response?.data?.detail || error.message
      throw new Error(`搜索文档失败: ${message}`)
    }
  }

  /**
   * 更新向量库文档
   * @param {Object} request - { ids: string[], texts: string[], metadatas?: Object[] }
   * @returns {Promise<Object>}
   */
  async vectorDBUpdate(request) {
    try {
      const response = await axios.post(`${this.baseUrl}/api/vectordb/update`, request)
      return response.data
    } catch (error) {
      const message = error.response?.data?.detail || error.message
      throw new Error(`更新文档失败: ${message}`)
    }
  }

  /**
   * 删除向量库文档
   * @param {Object} request - { ids?: string[], filter_meta?: Object }
   * @returns {Promise<Object>}
   */
  async vectorDBDelete(request) {
    // Mock 模式
    if (mockService.isEnabled()) {
      const docId = request.ids?.[0] || 'unknown'
      return await mockService.deleteDocument(docId)
    }

    // 真实 API
    try {
      const response = await axios.post(`${this.baseUrl}/api/vectordb/delete`, request)
      return response.data
    } catch (error) {
      const message = error.response?.data?.detail || error.message
      throw new Error(`删除文档失败: ${message}`)
    }
  }

  /**
   * 获取向量库文档列表
   * @param {number} limit - 限制数量，默认 100
   * @returns {Promise<Object>}
   */
  async vectorDBList(limit = 100) {
    try {
      const response = await axios.get(`${this.baseUrl}/api/vectordb/list?limit=${limit}`)
      return response.data
    } catch (error) {
      const message = error.response?.data?.detail || error.message
      throw new Error(`获取文档列表失败: ${message}`)
    }
  }

  // ========== 健康检查 ==========

  /**
   * 健康检查
   * @returns {Promise<Object>} { status: string }
   */
  async healthCheck() {
    try {
      const response = await axios.get(`${this.baseUrl}/api/health`)
      return response.data
    } catch (error) {
      throw new Error('健康检查失败')
    }
  }

  /**
   * 获取API信息
   * @returns {Promise<Object>} { message, version, status }
   */
  async getInfo() {
    try {
      const response = await axios.get(`${this.baseURL}/`)
      return response.data
    } catch (error) {
      throw new Error('获取API信息失败')
    }
  }
}

// 导出单例
export const apiClient = new APIClient()
export default apiClient
