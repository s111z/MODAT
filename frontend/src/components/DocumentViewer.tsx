'use client'

export default function DocumentViewer() {
  return (
    <div className="p-6">
      <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
        {/* 文档头部信息 */}
        <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                </svg>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">用户协议_v2.0.pdf</h3>
                <p className="text-xs text-gray-500">已上传 · 3.2 MB</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full font-medium">
                ● 已索引
              </span>
            </div>
          </div>
        </div>

        {/* 文档内容区域 */}
        <div className="p-8 max-h-[600px] overflow-y-auto">
          <div className="max-w-3xl mx-auto bg-gray-50 border border-gray-200 rounded-lg p-8 shadow-inner">
            <h2 className="text-center text-xl font-bold text-gray-900 mb-6">
              PREMIUM 会员订阅服务协议
            </h2>
            
            <div className="space-y-4 text-sm text-gray-700 leading-relaxed">
              <p>1. 服务条款的接受</p>
              <p className="pl-4">
                欢迎使用本平台的PREMIUM会员服务。在使用本服务前，请您仔细阅读并充分理解本协议的全部内容...
              </p>
              
              <p className="mt-6">4. 订阅与费用</p>
              <p className="pl-4">4.1 订阅费用将每年收取一次...</p>
              
              <div className="pl-4 my-4 p-4 bg-red-50 border-l-4 border-red-500 rounded">
                <p className="font-medium text-red-900">
                  4.2 用户可随时取消订阅。若需取消下个月的续费，请至少提前30天向客服邮箱 (support@app.com) 发送申请。若未发送，系统将默认自动续费一年。
                </p>
                <p className="text-xs text-red-600 mt-2">
                  ⚠️ 此条款可能存在合规风险
                </p>
              </div>
              
              <p className="pl-4">4.3 除非另有说明，否则所有费用概不退还...</p>
              
              <p className="mt-6">10. 争议解决</p>
              <p className="pl-4">
                本协议的订立、执行和解释及争议的解决均应适用中华人民共和国法律...
              </p>
            </div>
            
            <div className="mt-8 pt-4 border-t border-gray-300 text-center text-xs text-gray-500">
              — 文档结束 —
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}