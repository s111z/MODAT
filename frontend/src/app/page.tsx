'use client'

import { useState, useEffect } from 'react'
import ChatInterface from '@/components/ChatInterface'
import AgentThinking from '@/components/AgentThinking'
import DocumentReviewPanel from '@/components/DocumentReviewPanel'
import HistoryList from '@/components/HistoryList'
import GlobalSearch from '@/components/GlobalSearch'
import KnowledgeManager from '@/components/KnowledgeManager'

export default function Home() {
  const [agentSteps, setAgentSteps] = useState<Array<{
    id: string
    type: 'thinking' | 'searching' | 'parsing' | 'resolving' | 'generating'
    content: string
    timestamp: number
  }>>([])
  const [isAgentActive, setIsAgentActive] = useState(false)
  
  // 新增：侧边栏状态管理
  const [sidebarActive, setSidebarActive] = useState<'chat' | 'history' | 'search' | 'knowledge'>('chat')
  
  // 新增：任务模式状态
  const [taskMode, setTaskMode] = useState<'qa' | 'document-review'>('qa')
  
  // 新增：文档审核阶段状态
  const [reviewPhase, setReviewPhase] = useState<'document' | 'workflow' | 'result'>('document')

  // Mock数据演示效果
  useEffect(() => {
    const mockSteps = [
      {
        id: 'mock-1',
        type: 'thinking' as const,
        content: '正在理解用户问题：如何实现深度学习模型的优化？',
        timestamp: Date.now() - 5000
      },
      {
        id: 'mock-2',
        type: 'searching' as const,
        content: '正在使用DuckDuckGo搜索最新的优化技术...',
        timestamp: Date.now() - 4000
      },
      {
        id: 'mock-3',
        type: 'parsing' as const,
        content: '正在解析文档中的相关章节...',
        timestamp: Date.now() - 3000
      },
      {
        id: 'mock-4',
        type: 'resolving' as const,
        content: '正在对比网络资源与内部知识库的差异...',
        timestamp: Date.now() - 2000
      },
      {
        id: 'mock-5',
        type: 'generating' as const,
        content: '正在使用DeepSeek生成综合性回复...',
        timestamp: Date.now() - 1000
      }
    ]
    
    setAgentSteps(mockSteps)
  }, [])

  const handleStepsUpdate = (steps: string[]) => {
    setIsAgentActive(true)
    
    const newSteps = steps.map((step, index) => {
      // 根据步骤内容判断类型
      let type: 'thinking' | 'searching' | 'parsing' | 'resolving' | 'generating' = 'thinking'
      
      if (step.includes('搜索') || step.includes('DuckDuckGo')) {
        type = 'searching'
      } else if (step.includes('解析') || step.includes('文档')) {
        type = 'parsing'
      } else if (step.includes('分析') || step.includes('冲突') || step.includes('差异')) {
        type = 'resolving'
      } else if (step.includes('生成') || step.includes('DeepSeek')) {
        type = 'generating'
      }
      
      return {
        id: `step-${Date.now()}-${index}`,
        type,
        content: step,
        timestamp: Date.now()
      }
    })
    
    setAgentSteps(newSteps)
    
    // 如果步骤完成，延迟关闭激活状态
    setTimeout(() => {
      setIsAgentActive(false)
    }, 1000)
  }

  return (
    <div className="h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex overflow-hidden">
      {/* 侧边栏 */}
      <div className="w-16 border-r border-gray-200 bg-white flex flex-col items-center pt-6 gap-7 flex-shrink-0 shadow-sm">
        {/* 对话图标 */}
        <div 
          onClick={() => setSidebarActive('chat')}
          className={`w-6 h-6 cursor-pointer transition-colors ${
            sidebarActive === 'chat' ? 'text-blue-500' : 'text-gray-400 hover:text-gray-600'
          }`}
        >
          <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
        </div>
        
        {/* 历史会话图标 */}
        <div 
          onClick={() => setSidebarActive('history')}
          className={`w-6 h-6 cursor-pointer transition-colors ${
            sidebarActive === 'history' ? 'text-blue-500' : 'text-gray-400 hover:text-gray-600'
          }`}
        >
          <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
          </svg>
        </div>
        
        {/* 全局搜索图标 */}
        <div
          onClick={() => setSidebarActive('search')}
          className={`w-6 h-6 cursor-pointer transition-colors ${
            sidebarActive === 'search' ? 'text-blue-500' : 'text-gray-400 hover:text-gray-600'
          }`}
        >
          <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
        </div>

        {/* 知识库管理图标 */}
        <div
          onClick={() => setSidebarActive('knowledge')}
          className={`w-6 h-6 cursor-pointer transition-colors ${
            sidebarActive === 'knowledge' ? 'text-blue-500' : 'text-gray-400 hover:text-gray-600'
          }`}
        >
          <svg width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
            <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
          </svg>
        </div>
      </div>

      {/* 主内容区域 - 改为 45% vs 55% 双栏布局，小屏单栏 */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-[45%_55%] h-screen">
        {/* 左侧：动态面板 */}
        <div className="border-r border-gray-200 h-screen overflow-y-auto bg-white/50 backdrop-blur-sm transition-all duration-300 hidden lg:block">
          {sidebarActive === 'chat' && taskMode === 'qa' && (
            <AgentThinking 
              steps={agentSteps}
              isActive={isAgentActive}
            />
          )}
          {sidebarActive === 'chat' && taskMode === 'document-review' && (
            <DocumentReviewPanel 
              phase={reviewPhase}
              onPhaseChange={setReviewPhase}
              agentSteps={agentSteps}
              isActive={isAgentActive}
            />
          )}
          {sidebarActive === 'history' && <HistoryList />}
          {sidebarActive === 'search' && <GlobalSearch />}
          {sidebarActive === 'knowledge' && <KnowledgeManager />}
        </div>

        {/* 右侧：对话界面 */}
        <div className="h-screen transition-all duration-300">
          <ChatInterface 
            onStepsUpdate={handleStepsUpdate}
            onModeChange={setTaskMode}
            onReviewPhaseChange={setReviewPhase}
          />
        </div>
      </div>
    </div>
  );
}
