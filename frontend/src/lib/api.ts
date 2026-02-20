const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'

export interface ChatMessage {
  message: string
  mode?: 'qa' | 'review'
}

export interface ChatResponse {
  response: string
  steps: string[]
}

export interface ReviewRequest {
  filename: string
  message: string
  mode?: string
}

export interface StreamEvent {
  type: 'step' | 'response' | 'error'
  content: string
  steps?: string[]
}

// 向量库相关接口
export interface VectorDBAddRequest {
  filename: string
  metadatas?: {
    category?: string
    permissions?: number
  }
}

export interface VectorDBSearchRequest {
  query: string
  top_k?: number
  filter_meta?: Record<string, any>
}

export interface VectorDBUpdateRequest {
  ids: string[]
  texts: string[]
  metadatas?: Record<string, any>[]
}

export interface VectorDBDeleteRequest {
  ids?: string[]
  filter_meta?: Record<string, any>
}

export interface VectorDBResponse {
  success: boolean
  message: string
  results: Array<Record<string, any>>
  steps: string[]
}

export interface UploadResponse {
  savefilename: string
  size: number
  status: string
  message: string
}

export class APIClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  // ========== 聊天相关接口 ==========

  async chat(message: ChatMessage): Promise<ChatResponse> {
    const response = await fetch(`${this.baseUrl}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(message),
    })

    if (!response.ok) {
      throw new Error(`API请求失败: ${response.statusText}`)
    }

    return response.json()
  }

  async *chatStream(message: ChatMessage): AsyncGenerator<StreamEvent> {
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

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('无法读取响应流')
    }

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data.trim()) {
            try {
              yield JSON.parse(data) as StreamEvent
            } catch (e) {
              console.error('解析流数据失败:', e)
            }
          }
        }
      }
    }
  }

  async review(request: ReviewRequest): Promise<ChatResponse> {
    const response = await fetch(`${this.baseUrl}/api/review`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      throw new Error(`文档审核请求失败: ${response.statusText}`)
    }

    return response.json()
  }

  // ========== 文件上传接口 ==========

  async uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${this.baseUrl}/api/upload`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || `文件上传失败: ${response.statusText}`)
    }

    return response.json()
  }

  async uploadKnowledgeFile(file: File): Promise<UploadResponse> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${this.baseUrl}/api/knowledge_upload`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || `知识库文件上传失败: ${response.statusText}`)
    }

    return response.json()
  }

  // ========== 向量库管理接口 ==========

  async vectorDBAdd(request: VectorDBAddRequest): Promise<VectorDBResponse> {
    const response = await fetch(`${this.baseUrl}/api/vectordb/add`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || `添加文档失败: ${response.statusText}`)
    }

    return response.json()
  }

  async vectorDBSearch(request: VectorDBSearchRequest): Promise<VectorDBResponse> {
    const response = await fetch(`${this.baseUrl}/api/vectordb/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || `搜索文档失败: ${response.statusText}`)
    }

    return response.json()
  }

  async vectorDBUpdate(request: VectorDBUpdateRequest): Promise<VectorDBResponse> {
    const response = await fetch(`${this.baseUrl}/api/vectordb/update`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || `更新文档失败: ${response.statusText}`)
    }

    return response.json()
  }

  async vectorDBDelete(request: VectorDBDeleteRequest): Promise<VectorDBResponse> {
    const response = await fetch(`${this.baseUrl}/api/vectordb/delete`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || `删除文档失败: ${response.statusText}`)
    }

    return response.json()
  }

  async vectorDBList(limit: number = 10): Promise<VectorDBResponse> {
    const response = await fetch(`${this.baseUrl}/api/vectordb/list?limit=${limit}`, {
      method: 'GET',
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || `获取文档列表失败: ${response.statusText}`)
    }

    return response.json()
  }

  // ========== 健康检查 ==========

  async healthCheck(): Promise<{ status: string }> {
    const response = await fetch(`${this.baseUrl}/api/health`)

    if (!response.ok) {
      throw new Error('健康检查失败')
    }

    return response.json()
  }

  // ========== 根路径信息 ==========

  async getInfo(): Promise<{ message: string; version: string; status: string }> {
    const response = await fetch(`${this.baseUrl}/`)

    if (!response.ok) {
      throw new Error('获取API信息失败')
    }

    return response.json()
  }
}

export const apiClient = new APIClient()
