'use client'

import { useState, useEffect, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Input } from '@/components/ui/input'
import { Upload, Search, Trash2, FileText, CheckCircle, XCircle, Loader2, RefreshCw } from 'lucide-react'
import { apiClient, type VectorDBResponse } from '@/lib/api'

interface Document {
  id: string
  content: string
  metadata: {
    source?: string
    file_type?: string
    category?: string
    permissions?: number
    chunk_index?: number
    total_chunks?: number
    created_at?: string
  }
}

export default function KnowledgeManager() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<Document[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<{
    type: 'success' | 'error' | ''
    message: string
  }>({ type: '', message: '' })
  const [processingSteps, setProcessingSteps] = useState<string[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  // 加载文档列表
  const loadDocuments = async () => {
    setIsLoading(true)
    try {
      const response = await apiClient.vectorDBList(50)
      if (response.success) {
        setDocuments(response.results as Document[])
      }
    } catch (error) {
      console.error('加载文档列表失败:', error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadDocuments()
  }, [])

  // 文件上传处理
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    const file = files[0]
    setIsUploading(true)
    setUploadStatus({ type: '', message: '' })
    setProcessingSteps([])

    try {
      // 步骤1: 上传文件到服务器
      setProcessingSteps(['正在上传文件...'])
      const uploadResponse = await apiClient.uploadKnowledgeFile(file)

      setProcessingSteps(prev => [...prev, `文件上传成功: ${uploadResponse.savefilename}`])

      // 步骤2: 添加到向量库
      setProcessingSteps(prev => [...prev, '正在解析并添加到知识库...'])
      const addResponse = await apiClient.vectorDBAdd({
        filename: uploadResponse.savefilename,
        metadatas: {
          category: 'law', // 默认类别
          permissions: 0    // 公开文档
        }
      })

      // 显示所有步骤
      if (addResponse.steps && addResponse.steps.length > 0) {
        setProcessingSteps(prev => [...prev, ...addResponse.steps])
      }

      if (addResponse.success) {
        setUploadStatus({
          type: 'success',
          message: `${addResponse.message} - 文件已成功添加到知识库`
        })
        // 刷新文档列表
        await loadDocuments()
      } else {
        setUploadStatus({
          type: 'error',
          message: addResponse.message || '添加到知识库失败'
        })
      }
    } catch (error: any) {
      setUploadStatus({
        type: 'error',
        message: error.message || '处理失败'
      })
    } finally {
      setIsUploading(false)
      // 清空文件输入
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  // 搜索处理
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([])
      return
    }

    setIsSearching(true)
    try {
      const response = await apiClient.vectorDBSearch({
        query: searchQuery,
        top_k: 10
      })

      if (response.success) {
        setSearchResults(response.results as Document[])
      }
    } catch (error) {
      console.error('搜索失败:', error)
    } finally {
      setIsSearching(false)
    }
  }

  // 删除文档
  const handleDelete = async (docId: string) => {
    if (!confirm('确定要删除这个文档吗？')) return

    try {
      const response = await apiClient.vectorDBDelete({
        ids: [docId]
      })

      if (response.success) {
        // 刷新列表
        await loadDocuments()
        // 如果在搜索结果中，也更新搜索结果
        if (searchResults.length > 0) {
          setSearchResults(prev => prev.filter(doc => doc.id !== docId))
        }
      }
    } catch (error) {
      console.error('删除失败:', error)
      alert('删除失败')
    }
  }

  const displayedDocuments = searchResults.length > 0 ? searchResults : documents

  return (
    <div className="h-full flex flex-col bg-white">
      {/* 标题栏 */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <h2 className="text-lg font-semibold text-gray-900">知识库管理</h2>
        <p className="text-sm text-gray-500 mt-1">
          管理向量数据库中的文档，支持上传、搜索和删除
        </p>
      </div>

      {/* 上传区域 */}
      <div className="px-6 py-4 border-b border-gray-200">
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pdf"
          onChange={handleFileUpload}
          disabled={isUploading}
        />

        <Button
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          className="w-full bg-blue-500 hover:bg-blue-600 text-white"
        >
          {isUploading ? (
            <>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              处理中...
            </>
          ) : (
            <>
              <Upload className="h-4 w-4 mr-2" />
              上传PDF到知识库
            </>
          )}
        </Button>

        {/* 上传状态显示 */}
        {uploadStatus.type && (
          <div className={`mt-3 p-3 rounded-lg border ${
            uploadStatus.type === 'success'
              ? 'bg-green-50 border-green-200 text-green-700'
              : 'bg-red-50 border-red-200 text-red-700'
          }`}>
            <div className="flex items-start gap-2">
              {uploadStatus.type === 'success' ? (
                <CheckCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              ) : (
                <XCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
              )}
              <div className="flex-1">
                <p className="text-sm font-medium">{uploadStatus.message}</p>
                {processingSteps.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {processingSteps.map((step, index) => (
                      <p key={index} className="text-xs opacity-75">
                        • {step}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 搜索区域 */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex gap-2">
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="搜索知识库内容..."
            className="flex-1"
            disabled={isSearching}
          />
          <Button
            onClick={handleSearch}
            disabled={isSearching}
            variant="outline"
          >
            {isSearching ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
          </Button>
          <Button
            onClick={loadDocuments}
            disabled={isLoading}
            variant="outline"
            title="刷新列表"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>

        {searchResults.length > 0 && (
          <div className="mt-2 text-sm text-gray-600">
            找到 {searchResults.length} 个相关结果
            <Button
              variant="link"
              size="sm"
              onClick={() => {
                setSearchResults([])
                setSearchQuery('')
              }}
              className="ml-2"
            >
              清除搜索
            </Button>
          </div>
        )}
      </div>

      {/* 文档列表 */}
      <ScrollArea className="flex-1">
        <div className="px-6 py-4 space-y-3">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            </div>
          ) : displayedDocuments.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <FileText className="h-12 w-12 mx-auto mb-3 opacity-30" />
              <p>
                {searchQuery ? '未找到匹配的文档' : '知识库为空，请上传文档'}
              </p>
            </div>
          ) : (
            displayedDocuments.map((doc) => (
              <Card key={doc.id} className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-medium text-gray-900 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <FileText className="h-4 w-4 text-blue-500" />
                      <span className="truncate">
                        {doc.metadata?.source || doc.id}
                      </span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(doc.id)}
                      className="text-red-500 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-xs text-gray-600 line-clamp-3 mb-2">
                    {doc.content}
                  </p>
                  <div className="flex flex-wrap gap-2 text-xs text-gray-500">
                    {doc.metadata?.category && (
                      <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded">
                        {doc.metadata.category}
                      </span>
                    )}
                    {doc.metadata?.chunk_index !== undefined && (
                      <span className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                        Chunk {doc.metadata.chunk_index + 1}/{doc.metadata.total_chunks}
                      </span>
                    )}
                    {doc.metadata?.file_type && (
                      <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded">
                        {doc.metadata.file_type}
                      </span>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </ScrollArea>

      {/* 底部统计 */}
      <div className="px-6 py-3 border-t border-gray-200 bg-gray-50 text-sm text-gray-600">
        共 {documents.length} 个文档块
      </div>
    </div>
  )
}
