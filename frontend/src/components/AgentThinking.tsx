'use client'

import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Brain, Search, FileText, GitMerge, Sparkles } from 'lucide-react'

interface AgentStep {
  id: string
  type: 'thinking' | 'searching' | 'parsing' | 'resolving' | 'generating'
  content: string
  timestamp: number
}

interface AgentThinkingProps {
  steps: AgentStep[]
  isActive?: boolean
}

const stepIcons = {
  thinking: Brain,
  searching: Search,
  parsing: FileText,
  resolving: GitMerge,
  generating: Sparkles
}

const stepLabels = {
  thinking: '思考中',
  searching: '搜索中',
  parsing: '解析中',
  resolving: '分析中',
  generating: '生成中'
}

export default function AgentThinking({ steps, isActive = false }: AgentThinkingProps) {
  return (
    <div className="h-full bg-white border border-gray-200 rounded-lg overflow-hidden flex flex-col shadow-sm">
      {/* 头部 */}
      <div className="px-5 py-4 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="h-4 w-4 text-blue-500" />
          <span className="text-xs font-mono uppercase text-gray-600 font-bold tracking-wider">
            代理思维过程
          </span>
        </div>
        {isActive && (
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse"></div>
            <span className="text-xs text-blue-500 font-mono">Running</span>
          </div>
        )}
      </div>

      {/* 思考流区域 */}
      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
        {steps.length === 0 && !isActive ? (
          <div className="flex items-center justify-center h-full text-gray-400 text-sm">
            等待任务执行...
          </div>
        ) : (
          steps.map((step, index) => {
            const Icon = stepIcons[step.type]
            return (
              <div 
                key={step.id}
                className="bg-gray-50 border border-gray-200 rounded-lg p-4 animate-in fade-in slide-in-from-bottom-2 duration-500 hover:bg-gray-100 transition-colors"
                style={{ animationDelay: `${index * 100}ms` }}
              >
                <div className="flex items-center gap-2 mb-3">
                  <Icon className="h-3.5 w-3.5 text-blue-500" />
                  <span className="text-xs font-mono uppercase text-blue-600 font-bold tracking-wider">
                    {stepLabels[step.type]}
                  </span>
                </div>
                <p className="text-sm text-gray-700 leading-relaxed">
                  {step.content}
                </p>
                <p className="text-xs text-gray-400 mt-2 font-mono">
                  {new Date(step.timestamp).toLocaleTimeString()}
                </p>
              </div>
            )
          })
        )}
        
        {isActive && (
          <div className="flex items-center justify-center gap-2 py-4">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
            <span className="text-xs text-gray-500">代理正在工作中...</span>
          </div>
        )}
      </div>
    </div>
  )
}