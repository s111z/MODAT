'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Send, Paperclip, X } from 'lucide-react'
import { apiClient } from '@/lib/api'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  steps?: string[]
  files?: string[]
}

interface ChatInterfaceProps {
  onStepsUpdate?: (steps: string[]) => void
  onModeChange?: (mode: 'qa' | 'document-review') => void
  onReviewPhaseChange?: (phase: 'document' | 'workflow' | 'result') => void
}

export default function ChatInterface({ onStepsUpdate, onModeChange, onReviewPhaseChange }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [currentSteps, setCurrentSteps] = useState<string[]>([])
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Mock数据演示
  useEffect(() => {
    const mockMessages: Message[] = [
      {
        id: 'mock-1',
        role: 'user',
        content: '请帮我分析一下深度学习模型优化的最佳实践',
        files: []
      },
      {
        id: 'mock-2',
        role: 'assistant',
        content: '根据我的分析和搜索结果，深度学习模型优化的最佳实践包括以下几个方面：\n\n1. **学习率调整**：使用学习率衰减策略，如余弦退火或步进衰减\n2. **批量大小优化**：根据GPU内存选择合适的batch size\n3. **正则化技术**：应用Dropout、L2正则化等防止过拟合\n4. **数据增强**：通过数据增强提高模型泛化能力\n5. **模型架构**：选择合适的网络结构，考虑使用预训练模型\n\n这些建议综合了网络搜索结果和内部知识库的最佳实践。',
        steps: [
          '正在理解用户问题：如何实现深度学习模型的优化？',
          '正在使用DuckDuckGo搜索最新的优化技术...',
          '找到 5 条搜索结果',
          '正在检索内部知识库...',
          '检测到多源信息，正在进行一致性分析...',
          '正在使用DeepSeek生成回复...',
          '已使用DeepSeek生成回复'
        ]
      }
    ]
    setMessages(mockMessages)
  }, [])

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      const file = files[0]

      try {
        // 上传文件到后端
        const uploadResponse = await apiClient.uploadFile(file)

        // 保存上传文件信息（包括服务器返回的文件名）
        const fileInfo = {
          originalFile: file,
          serverFilename: uploadResponse.savefilename
        }

        setUploadedFiles(prev => [...prev, file])

        // 存储服务器文件名供后续使用
        if (fileInputRef.current) {
          fileInputRef.current.dataset.serverFilename = uploadResponse.savefilename
        }

        // 检测文件上传，切换到文档审核模式
        if (onModeChange) {
          onModeChange('document-review')
        }
        // 自动切换到文档预览阶段
        if (onReviewPhaseChange) {
          onReviewPhaseChange('document')
        }
      } catch (error) {
        console.error('文件上传失败:', error)
        alert('文件上传失败，请重试')
      }
    }
  }

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleSend = async () => {
    if (!input.trim()) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input
    }

    setMessages(prev => [...prev, userMessage])
    const query = input
    setInput('')
    setIsLoading(true)
    setCurrentSteps([])

    try {
      // 使用流式API
      const streamGenerator = apiClient.chatStream({
        message: query,
        mode: 'qa'
      })

      const steps: string[] = []
      let finalResponse = ''

      for await (const event of streamGenerator) {
        if (event.type === 'step') {
          steps.push(event.content)
          setCurrentSteps([...steps])
          if (onStepsUpdate) {
            onStepsUpdate([...steps])
          }
        } else if (event.type === 'response') {
          finalResponse = event.content
          if (event.steps) {
            steps.push(...event.steps)
          }
        } else if (event.type === 'error') {
          console.error('API错误:', event.content)
          finalResponse = `错误: ${event.content}`
        }
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: finalResponse || '抱歉，未能生成回复',
        steps: steps
      }
      
      setMessages(prev => [...prev, assistantMessage])
      setIsLoading(false)
      setCurrentSteps([])
      
    } catch (error) {
      console.error('发送消息失败:', error)
      
      // 降级到非流式API
      try {
        const response = await apiClient.chat({
          message: query,
          mode: 'qa'
        })
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.response,
          steps: response.steps
        }
        
        setMessages(prev => [...prev, assistantMessage])
        if (onStepsUpdate) {
          onStepsUpdate(response.steps)
        }
      } catch (fallbackError) {
        console.error('备用API也失败:', fallbackError)
        
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: '抱歉，连接后端服务失败。请确保后端服务正在运行。',
          steps: []
        }
        
        setMessages(prev => [...prev, errorMessage])
      }
      
      setIsLoading(false)
      setCurrentSteps([])
    }
  }

  return (
    <div className="h-full flex flex-col relative bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
      {/* 顶部状态栏 */}
      <div className="px-6 py-4 flex items-center gap-3 border-b border-gray-200 bg-gray-50 z-10">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-100 to-indigo-100 flex items-center justify-center border border-gray-300">
          <div className={`w-1.5 h-1.5 rounded-full ${isLoading ? 'bg-blue-500 animate-pulse' : 'bg-gray-400'}`}></div>
        </div>
        <div>
          <div className="font-semibold text-sm text-gray-900">Compliance Copilot</div>
          <div className="text-xs text-gray-500 font-mono">
            {isLoading ? 'Processing...' : 'Ready'}
          </div>
        </div>
      </div>

      {/* 对话区域 */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="space-y-4 pb-32">
          {messages.map((message) => (
            <div key={message.id} className="animate-in fade-in slide-in-from-bottom-2 duration-500">
              {message.role === 'user' ? (
                <div className="flex justify-end">
                  <div className="max-w-[85%] bg-blue-500 text-white rounded-lg px-4 py-3 shadow-sm">
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    {message.files && message.files.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-blue-400/30 text-xs">
                        📎 {message.files.join(', ')}
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="flex justify-start">
                  <div className="max-w-[85%] bg-gray-100 border border-gray-200 rounded-lg px-4 py-3">
                    <p className="text-sm text-gray-900 whitespace-pre-wrap leading-relaxed">
                      {message.content}
                    </p>
                  </div>
                </div>
              )}
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start animate-in fade-in duration-300">
              <div className="bg-gray-100 border border-gray-200 rounded-lg px-4 py-3">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  <p className="text-sm text-gray-600 ml-2">正在思考...</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 底部输入区域（固定） */}
      <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-white via-white/95 to-transparent pointer-events-none z-20">
        <div className="pointer-events-auto space-y-3">
          {/* 已上传文件 */}
          {uploadedFiles.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-3">
              {uploadedFiles.map((file, index) => (
                <div 
                  key={index} 
                  className="flex items-center gap-2 bg-white border border-gray-300 px-3 py-1.5 rounded-full text-xs text-gray-700 shadow-sm"
                >
                  <span className="truncate max-w-[180px]">{file.name}</span>
                  <button
                    onClick={() => removeFile(index)}
                    className="text-gray-400 hover:text-red-500 transition-colors"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* 输入框 */}
          <div className="h-14 bg-white border border-gray-300 rounded-full flex items-center px-2 shadow-lg hover:border-gray-400 transition-colors">
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              multiple
              accept=".pdf,.doc,.docx,.txt"
              onChange={handleFileSelect}
            />
            <Button
              variant="ghost"
              size="icon"
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading}
              className="text-gray-500 hover:text-gray-700 hover:bg-gray-100"
            >
              <Paperclip className="h-4 w-4" />
            </Button>
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
              placeholder="输入您的问题，或上传文档进行分析..."
              disabled={isLoading}
              className="flex-1 bg-transparent border-none text-gray-900 placeholder:text-gray-400 focus-visible:ring-0 focus-visible:ring-offset-0"
            />
            <Button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="w-11 h-11 rounded-full bg-blue-500 text-white hover:bg-blue-600 hover:scale-105 transition-transform disabled:opacity-50 disabled:hover:scale-100"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
          
          <p className="text-xs text-gray-500 px-4 text-center">
            💡 支持上传PDF、Word、TXT文档进行智能分析
          </p>
        </div>
      </div>
    </div>
  )
}