'use client'

import { FileText, Cog, CheckCircle } from 'lucide-react'
import AgentThinking from '@/components/AgentThinking'
import DocumentViewer from '@/components/DocumentViewer'
import ReviewReport from '@/components/ReviewReport'

interface DocumentReviewPanelProps {
  phase: 'document' | 'workflow' | 'result'
  onPhaseChange: (phase: 'document' | 'workflow' | 'result') => void
  agentSteps?: Array<{
    id: string
    type: 'thinking' | 'searching' | 'parsing' | 'resolving' | 'generating'
    content: string
    timestamp: number
  }>
  isActive?: boolean
}

export default function DocumentReviewPanel({ 
  phase, 
  onPhaseChange,
  agentSteps = [],
  isActive = false
}: DocumentReviewPanelProps) {
  return (
    <div className="h-full flex flex-col bg-white">
      {/* 顶部Tab切换栏 */}
      <div className="flex gap-2 px-4 py-3 border-b border-gray-200 bg-gray-50">
        <button
          onClick={() => onPhaseChange('document')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            phase === 'document'
              ? 'bg-blue-500 text-white shadow-sm'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          <FileText className="h-4 w-4" />
          文档预览
        </button>
        <button
          onClick={() => onPhaseChange('workflow')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            phase === 'workflow'
              ? 'bg-blue-500 text-white shadow-sm'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          <Cog className="h-4 w-4" />
          工作流程
        </button>
        <button
          onClick={() => onPhaseChange('result')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            phase === 'result'
              ? 'bg-blue-500 text-white shadow-sm'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          <CheckCircle className="h-4 w-4" />
          审核结果
        </button>
      </div>

      {/* 内容区域 */}
      <div className="flex-1 overflow-y-auto">
        {phase === 'document' && <DocumentViewer />}
        
        {phase === 'workflow' && (
          <div className="h-full">
            <AgentThinking steps={agentSteps} isActive={isActive} />
          </div>
        )}
        
        {phase === 'result' && <ReviewReport />}
      </div>
    </div>
  )
}
