'use client'

import { useState } from 'react'
import { Search, MessageSquare, Clock, ChevronRight } from 'lucide-react'

interface HistorySession {
  id: string
  title: string
  preview: string
  timestamp: Date
  messageCount: number
}

export default function HistoryList() {
  const [searchQuery, setSearchQuery] = useState('')
  
  // Mock历史会话数据
  const mockSessions: HistorySession[] = [
    {
      id: '1',
      title: '深度学习模型优化咨询',
      preview: '请帮我分析一下深度学习模型优化的最佳实践...',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2小时前
      messageCount: 8
    },
    {
      id: '2',
      title: 'Python异步编程问题',
      preview: '在使用asyncio时遇到了一些问题，能否帮我看看...',
      timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000), // 1天前
      messageCount: 12
    },
    {
      id: '3',
      title: 'React性能优化方案',
      preview: '我的React应用性能较差，想了解一下优化方案...',
      timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000), // 3天前
      messageCount: 6
    },
    {
      id: '4',
      title: '数据库索引设计讨论',
      preview: 'MySQL数据库在大数据量下查询很慢，如何优化索引...',
      timestamp: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // 7天前
      messageCount: 15
    }
  ]

  const filteredSessions = mockSessions.filter(session =>
    session.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    session.preview.toLowerCase().includes(searchQuery.toLowerCase())
  )

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

  return (
    <div className="h-full flex flex-col bg-white">
      {/* 头部 */}
      <div className="px-5 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-2 mb-3">
          <MessageSquare className="h-4 w-4 text-blue-500" />
          <span className="text-xs font-mono uppercase text-gray-600 font-bold tracking-wider">
            历史会话
          </span>
        </div>
        
        {/* 搜索框 */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="搜索历史会话..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-white border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {/* 会话列表 */}
      <div className="flex-1 overflow-y-auto">
        {filteredSessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400 px-6">
            <MessageSquare className="h-12 w-12 mb-3 opacity-30" />
            <p className="text-sm text-center">
              {searchQuery ? '未找到匹配的会话' : '暂无历史会话'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {filteredSessions.map((session) => (
              <div
                key={session.id}
                className="px-5 py-4 hover:bg-blue-50 cursor-pointer transition-colors group"
                onClick={() => {
                  // TODO: 加载会话到对话区
                  console.log('Load session:', session.id)
                }}
              >
                <div className="flex items-start justify-between mb-2">
                  <h3 className="font-medium text-gray-900 text-sm group-hover:text-blue-600 transition-colors">
                    {session.title}
                  </h3>
                  <ChevronRight className="h-4 w-4 text-gray-400 group-hover:text-blue-500 flex-shrink-0 ml-2" />
                </div>
                
                <p className="text-xs text-gray-500 line-clamp-2 mb-2">
                  {session.preview}
                </p>
                
                <div className="flex items-center gap-4 text-xs text-gray-400">
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    <span>{formatTimestamp(session.timestamp)}</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <MessageSquare className="h-3 w-3" />
                    <span>{session.messageCount} 条消息</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}