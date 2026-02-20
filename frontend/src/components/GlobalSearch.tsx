'use client'

import { useState } from 'react'
import { Search, MessageSquare, Clock, FileText } from 'lucide-react'

interface SearchResult {
  id: string
  sessionId: string
  sessionTitle: string
  matchedContent: string
  timestamp: Date
  context: string
}

export default function GlobalSearch() {
  const [searchQuery, setSearchQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  
  // Mock搜索结果数据
  const mockResults: SearchResult[] = searchQuery.length >= 2 ? [
    {
      id: '1',
      sessionId: 'session-1',
      sessionTitle: '深度学习模型优化咨询',
      matchedContent: '学习率调整：使用学习率衰减策略，如余弦退火或步进衰减',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
      context: '根据我的分析和搜索结果，深度学习模型优化的最佳实践包括以下几个方面：学习率调整...'
    },
    {
      id: '2',
      sessionId: 'session-3',
      sessionTitle: 'React性能优化方案',
      matchedContent: '使用React.memo和useMemo进行性能优化',
      timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000),
      context: 'React性能优化可以从多个方面入手，使用React.memo和useMemo可以避免不必要的重渲染...'
    },
    {
      id: '3',
      sessionId: 'session-2',
      sessionTitle: 'Python异步编程问题',
      matchedContent: '异步IO操作可以显著提升程序性能',
      timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000),
      context: '在使用asyncio时，异步IO操作可以显著提升程序性能，特别是在处理大量并发请求时...'
    }
  ] : []

  const highlightMatch = (text: string, query: string) => {
    if (!query) return text
    const regex = new RegExp(`(${query})`, 'gi')
    const parts = text.split(regex)
    return parts.map((part, index) =>
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200 text-gray-900 font-medium">
          {part}
        </mark>
      ) : (
        part
      )
    )
  }

  const formatTimestamp = (date: Date) => {
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 60) return `${diffMins}分钟前`
    if (diffHours < 24) return `${diffHours}小时前`
    if (diffDays < 7) return `${diffDays}天前`
    return date.toLocaleDateString('zh-CN')
  }

  const handleSearch = (query: string) => {
    setSearchQuery(query)
    if (query.length >= 2) {
      setIsSearching(true)
      // 模拟搜索延迟
      setTimeout(() => setIsSearching(false), 300)
    }
  }

  return (
    <div className="h-full flex flex-col bg-white">
      {/* 头部 */}
      <div className="px-5 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-2 mb-3">
          <Search className="h-4 w-4 text-blue-500" />
          <span className="text-xs font-mono uppercase text-gray-600 font-bold tracking-wider">
            全局搜索
          </span>
        </div>
        
        {/* 搜索框 */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="搜索所有会话中的内容..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            autoFocus
          />
        </div>
        
        {searchQuery && (
          <p className="text-xs text-gray-500 mt-2">
            找到 {mockResults.length} 条结果
          </p>
        )}
      </div>

      {/* 搜索结果列表 */}
      <div className="flex-1 overflow-y-auto">
        {!searchQuery ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400 px-6">
            <Search className="h-12 w-12 mb-3 opacity-30" />
            <p className="text-sm text-center">
              输入关键词搜索所有会话内容
            </p>
            <p className="text-xs text-gray-400 mt-1">
              至少输入2个字符
            </p>
          </div>
        ) : isSearching ? (
          <div className="flex items-center justify-center h-32">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
          </div>
        ) : mockResults.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400 px-6">
            <FileText className="h-12 w-12 mb-3 opacity-30" />
            <p className="text-sm text-center">
              未找到匹配的内容
            </p>
            <p className="text-xs text-gray-400 mt-1">
              尝试使用不同的关键词
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {mockResults.map((result) => (
              <div
                key={result.id}
                className="px-5 py-4 hover:bg-blue-50 cursor-pointer transition-colors group"
                onClick={() => {
                  // TODO: 跳转到对应会话
                  console.log('Jump to session:', result.sessionId)
                }}
              >
                {/* 会话标题 */}
                <div className="flex items-center gap-2 mb-2">
                  <MessageSquare className="h-3 w-3 text-gray-400" />
                  <span className="text-xs text-gray-500">
                    {result.sessionTitle}
                  </span>
                  <Clock className="h-3 w-3 text-gray-400 ml-auto" />
                  <span className="text-xs text-gray-400">
                    {formatTimestamp(result.timestamp)}
                  </span>
                </div>
                
                {/* 匹配内容 */}
                <p className="text-sm text-gray-900 font-medium mb-2 group-hover:text-blue-600">
                  {highlightMatch(result.matchedContent, searchQuery)}
                </p>
                
                {/* 上下文 */}
                <p className="text-xs text-gray-500 line-clamp-2">
                  {highlightMatch(result.context, searchQuery)}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}