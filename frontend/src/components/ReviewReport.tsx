'use client'

import { AlertTriangle, CheckCircle, XCircle, Lightbulb } from 'lucide-react'

export default function ReviewReport() {
  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* 审核概览卡片 */}
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
          <div className="px-6 py-4 bg-gradient-to-r from-red-50 to-orange-50 border-b border-red-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center">
                  <span className="text-2xl font-bold text-red-600">D</span>
                </div>
                <div>
                  <h2 className="text-lg font-bold text-gray-900">合规审查报告</h2>
                  <p className="text-sm text-gray-600">德国 · 2022公平消费者合同法</p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs text-gray-500">风险评级</div>
                <div className="text-2xl font-bold text-red-600">高风险</div>
              </div>
            </div>
          </div>

          {/* 关键发现 */}
          <div className="p-6">
            <div className="flex items-start gap-3 mb-4">
              <XCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-semibold text-red-900 mb-2">发现高风险违规 (2项)</h3>
                <ul className="space-y-3 text-sm text-gray-700">
                  <li className="flex items-start gap-2">
                    <span className="text-red-500 font-bold">•</span>
                    <div>
                      <span className="font-medium">暗黑模式 (Dark Pattern)：</span>
                      <span className="ml-1">条款4.2仅提供邮件退订方式，违反"取消按钮"强制性义务。根据2022德国新规，必须在用户界面提供一键取消功能。</span>
                    </div>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-red-500 font-bold">•</span>
                    <div>
                      <span className="font-medium">期限陷阱：</span>
                      <span className="ml-1">默认自动续费12个月被视为无效条款。德国法律要求订阅服务的自动续费周期不得超过1个月，除非用户主动选择更长周期。</span>
                    </div>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* 详细分析 */}
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-orange-500" />
            详细分析
          </h3>
          
          <div className="space-y-4 text-sm text-gray-700">
            <div className="pl-4 border-l-2 border-orange-300">
              <p className="font-medium text-gray-900 mb-1">问题条款位置：</p>
              <p>文档第4.2条 "订阅与费用" 章节</p>
            </div>
            
            <div className="pl-4 border-l-2 border-blue-300">
              <p className="font-medium text-gray-900 mb-1">法律依据：</p>
              <p>《德国公平消费者合同法》2022年修订版 第312g条</p>
              <p className="mt-1 text-xs text-gray-600">
                "所有在线订阅服务必须提供与注册同等便利的取消机制，且续费周期不得超过一个月，除非消费者明确选择更长周期。"
              </p>
            </div>
            
            <div className="pl-4 border-l-2 border-red-300">
              <p className="font-medium text-gray-900 mb-1">风险评估：</p>
              <p>• 潜在罚款：最高可达年营业额的4%</p>
              <p>• 用户诉讼风险：高</p>
              <p>• 监管机构关注度：极高</p>
            </div>
          </div>
        </div>

        {/* AI修改建议 */}
        <div className="bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200 rounded-lg shadow-sm p-6">
          <h3 className="font-semibold text-green-900 mb-4 flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-green-600" />
            AI 修改建议
          </h3>
          
          <div className="space-y-4 text-sm text-gray-800">
            <div className="bg-white rounded-lg p-4 border border-green-200">
              <p className="font-medium text-green-900 mb-2">✅ 建议 1：添加一键取消按钮</p>
              <p className="mb-2">在用户账户设置页面增加明显的 <span className="px-2 py-0.5 bg-gray-100 rounded font-mono text-xs">[取消订阅]</span> 按钮。</p>
              <div className="mt-2 p-3 bg-gray-50 rounded text-xs font-mono">
                UI位置：账户设置 → 订阅管理 → 取消订阅按钮<br/>
                操作流程：点击按钮 → 确认弹窗 → 立即取消
              </div>
            </div>
            
            <div className="bg-white rounded-lg p-4 border border-green-200">
              <p className="font-medium text-green-900 mb-2">✅ 建议 2：调整自动续费周期</p>
              <p className="mb-2">将默认续费周期从"12个月"改为"按月续费"，并允许用户选择优惠的年度套餐。</p>
              <div className="mt-2 p-3 bg-gray-50 rounded text-xs">
                修改条款4.2为：<br/>
                <span className="italic">"用户订阅将按月自动续费。用户可随时通过账户设置中的[取消订阅]按钮取消服务。如需享受年度优惠，可在订阅时选择年度套餐。"</span>
              </div>
            </div>
            
            <div className="bg-white rounded-lg p-4 border border-green-200">
              <p className="font-medium text-green-900 mb-2">✅ 建议 3：增加续费提醒</p>
              <p>在续费前7天通过邮件和App推送提醒用户即将续费，并附带快速取消链接。</p>
            </div>
          </div>
        </div>

        {/* 时间戳 */}
        <div className="text-center text-xs text-gray-500">
          报告生成时间：{new Date().toLocaleString('zh-CN')}
        </div>
      </div>
    </div>
  )
}