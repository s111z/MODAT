import mockConfig from './config.json'
import knowledgeQAData from './knowledgeQA.json'

class MockService {
  constructor() {
    this.config = mockConfig
    this.knowledgeQAConfig = knowledgeQAData
    this.currentConversationIndex = {
      qa: 0,
      documentReview: 0,
      knowledgeQA: 0
    }
  }

  /**
   * 获取知识问答场景的下一个对话
   */
  getNextKnowledgeQAConversation() {
    const conversations = this.knowledgeQAConfig.conversations
    if (conversations.length === 0) return null

    const conversation = conversations[this.currentConversationIndex.knowledgeQA]
    this.currentConversationIndex.knowledgeQA =
      (this.currentConversationIndex.knowledgeQA + 1) % conversations.length

    return conversation
  }

  /**
   * 模拟知识问答消息发送（带工作流）
   * @param {string} message - 用户消息
   * @param {Function} onWorkflowUpdate - 工作流更新回调
   * @param {Function} onMessageStream - 消息流式输出回调
   */
  async sendKnowledgeQAMessage(message, onWorkflowUpdate, onMessageStream) {
    if (!this.isEnabled()) {
      throw new Error('Mock mode is not enabled')
    }

    const conversation = this.getNextKnowledgeQAConversation()
    if (!conversation) {
      if (onMessageStream) {
        onMessageStream('抱歉，没有可用的 Mock 数据')
      }
      return
    }

    const steps = conversation.agentWorkflow.steps
    const stepDelays = this.knowledgeQAConfig.agentWorkflow.stepDelays
    const streamConfig = this.knowledgeQAConfig.streamConfig

    // 初始化工作流步骤
    const workflowSteps = steps.map(step => ({
      ...step,
      status: 'pending',
      expanded: false
    }))

    // 更新初始状态
    if (onWorkflowUpdate) {
      onWorkflowUpdate([...workflowSteps])
    }

    // 执行工作流步骤
    for (let i = 0; i < workflowSteps.length; i++) {
      const step = workflowSteps[i]

      // 设置为processing状态
      workflowSteps[i].status = 'processing'
      if (onWorkflowUpdate) {
        onWorkflowUpdate([...workflowSteps])
      }

      // 等待步骤执行延迟
      const delayKey = this.getDelayKey(step.id)
      const delay = stepDelays[delayKey] || 800
      await this.delay(delay)

      // 设置为completed状态
      workflowSteps[i].status = 'completed'
      if (onWorkflowUpdate) {
        onWorkflowUpdate([...workflowSteps])
      }
    }

    // 流式输出回复
    if (onMessageStream && streamConfig.enabled) {
      const text = conversation.assistantMessage
      const charsPerSecond = streamConfig.charsPerSecond
      const charInterval = 1000 / charsPerSecond

      let currentIndex = 0
      let accumulatedText = ''

      while (currentIndex < text.length) {
        const char = text[currentIndex]
        accumulatedText += char
        currentIndex++

        onMessageStream(accumulatedText)
        await this.delay(charInterval)
      }
    } else if (onMessageStream) {
      // 如果不启用流式输出，直接返回完整文本
      onMessageStream(conversation.assistantMessage)
    }
  }

  /**
   * 根据步骤ID获取延迟配置的key
   */
  getDelayKey(stepId) {
    const keyMap = {
      'query-analysis': 'queryAnalysis',
      'query-construction': 'queryConstruction',
      'knowledge-retrieval': 'knowledgeRetrieval',
      'web-retrieval': 'webRetrieval',
      'multi-source-pk': 'multiSourcePK',
      'response-generation': 'responseGeneration'
    }
    return keyMap[stepId] || 'default'
  }

  /**
   * 检查是否启用 Mock 模式
   */
  isEnabled() {
    return this.config.enabled
  }

  /**
   * 获取 QA 场景的下一个对话（新版 config 已无此场景，返回 null）
   */
  getNextQAConversation() {
    const conversations = this.config.scenarios?.qa?.conversations
    if (!conversations || conversations.length === 0) return null

    const conversation = conversations[this.currentConversationIndex.qa]
    this.currentConversationIndex.qa = (this.currentConversationIndex.qa + 1) % conversations.length

    return conversation
  }

  /**
   * 获取文档审核场景的下一个对话
   */
  getNextDocumentReviewConversation() {
    const conversations = this.config.scenarios.documentReview.conversations
    if (conversations.length === 0) return null

    const conversation = conversations[this.currentConversationIndex.documentReview]
    this.currentConversationIndex.documentReview =
      (this.currentConversationIndex.documentReview + 1) % conversations.length

    return conversation
  }

  /**
   * 模拟发送消息（QA 场景）
   * @param {string} message - 用户消息
   * @returns {Promise} - 返回助手响应和 agent 步骤
   */
  async sendQAMessage(message) {
    if (!this.isEnabled()) {
      throw new Error('Mock mode is not enabled')
    }

    // 模拟网络延迟
    await this.delay(800)

    const conversation = this.getNextQAConversation()
    if (!conversation) {
      return {
        response: '抱歉，没有可用的 Mock 数据',
        steps: []
      }
    }

    return {
      response: conversation.assistantMessage,
      steps: conversation.agentSteps
    }
  }

  /**
   * 模拟流式响应（QA 场景）
   * @param {string} message - 用户消息
   * @param {Function} onStep - 步骤回调
   * @param {Function} onResponse - 响应回调
   */
  async sendQAMessageStream(message, onStep, onResponse) {
    if (!this.isEnabled()) {
      throw new Error('Mock mode is not enabled')
    }

    const conversation = this.getNextQAConversation()
    if (!conversation) {
      onResponse('抱歉，没有可用的 Mock 数据')
      return
    }

    // 模拟步骤流式输出
    for (const step of conversation.agentSteps) {
      await this.delay(600)
      if (onStep) {
        onStep({
          type: 'step',
          content: step.content,
          stepType: step.type
        })
      }
    }

    // 模拟响应流式输出（分段输出）
    const responseChunks = this.chunkText(conversation.assistantMessage, 20)
    for (const chunk of responseChunks) {
      await this.delay(50)
      if (onResponse) {
        onResponse({
          type: 'response',
          content: chunk
        })
      }
    }
  }

  /**
   * 模拟文档上传
   * @param {File} file - 上传的文件
   */
  async uploadFile(file) {
    if (!this.isEnabled()) {
      throw new Error('Mock mode is not enabled')
    }

    await this.delay(1000)

    return {
      success: true,
      savefilename: `mock_${Date.now()}_${file.name}`,
      message: '文件上传成功（Mock）'
    }
  }

  /**
   * 模拟发送消息（文档审核场景） - 流程式
   * @param {string} message - 用户消息
   * @param {Function} onPhaseChange - 阶段变化回调
   * @param {Function} onStepUpdate - 步骤更新回调
   * @param {Function} onResponse - 响应回调
   */
  async sendDocumentReviewMessageWithWorkflow(message, onPhaseChange, onStepUpdate, onResponse) {
    if (!this.isEnabled()) {
      throw new Error('Mock mode is not enabled')
    }

    const conversation = this.getNextDocumentReviewConversation()
    if (!conversation) {
      if (onResponse) {
        onResponse('抱歉，没有可用的 Mock 数据')
      }
      return
    }

    const reviewData = conversation.reviewData

    // 初始化工作流步骤数组（用于单栏模式）
    const steps = reviewData.workflow.steps
    const workflowSteps = steps.map(step => ({
      id: step.id,
      name: step.name,
      icon: step.icon,
      status: 'pending',
      expandable: true,
      expanded: false,
      details: step.details
    }))

    // 阶段1: 文档预览
    if (onPhaseChange) {
      onPhaseChange('document')
    }
    await this.delay(1000)

    // 显示文档内容（同时传递 fileName）
    if (onStepUpdate) {
      onStepUpdate({
        phase: 'document',
        content: reviewData.documentContent,
        fileName: conversation.fileName
      })
    }

    // 扫描动画
    await this.delay(2000)
    if (onStepUpdate) {
      onStepUpdate({
        phase: 'document',
        scanning: true
      })
    }
    await this.delay(2000)

    // 阶段2: 工作流程
    if (onPhaseChange) {
      onPhaseChange('workflow')
    }

    // 逐步执行工作流程
    for (let i = 0; i < steps.length; i++) {
      const step = steps[i]

      // 更新步骤状态为 in_progress
      workflowSteps[i].status = 'processing'
      if (onStepUpdate) {
        onStepUpdate({
          phase: 'workflow',
          stepIndex: i,
          status: 'in_progress',
          step: step,
          workflowSteps: [...workflowSteps] // 传递完整的工作流状态
        })
      }

      // 如果是 mcp-routing（多个 server 并行）
      if (step.id === 'mcp-routing') {
        await this.delay(600)
        if (step.details && step.details.servers) {
          for (const server of step.details.servers) {
            server.status = 'processing'
            if (onStepUpdate) {
              onStepUpdate({
                phase: 'workflow',
                stepIndex: i,
                status: 'in_progress',
                step: step,
                progressItem: server
              })
            }
            await this.delay(600)
            if (server.results) {
              for (const result of server.results) {
                if (onStepUpdate) {
                  onStepUpdate({
                    phase: 'workflow',
                    stepIndex: i,
                    status: 'in_progress',
                    step: step,
                    progressItem: result
                  })
                }
                await this.delay(300)
              }
            }
            server.status = 'done'
          }
        }
      } else if (step.id === 'knowledge-retrieval' || step.id === 'web-retrieval') {
        // 知识库检索和网络检索并行
        if (step.id === 'knowledge-retrieval') {
          // 开始知识库检索
          await this.delay(800)
          // 逐条显示检索结果
          if (step.details && step.details.results) {
            for (const result of step.details.results) {
              if (onStepUpdate) {
                onStepUpdate({
                  phase: 'workflow',
                  stepIndex: i,
                  status: 'in_progress',
                  step: step,
                  progressItem: result
                })
              }
              await this.delay(400)
            }
          }
        } else if (step.id === 'web-retrieval') {
          // 网络检索（与知识库检索同时进行）
          await this.delay(1000)
          if (step.details && step.details.results) {
            for (const result of step.details.results) {
              if (onStepUpdate) {
                onStepUpdate({
                  phase: 'workflow',
                  stepIndex: i,
                  status: 'in_progress',
                  step: step,
                  progressItem: result
                })
              }
              await this.delay(400)
            }
          }
        }
      } else if (step.id === 'report-generation' || step.id === 'response-generation') {
        // 报告生成和回复生成并行
        await this.delay(1000)
        if (step.details) {
          // 显示生成进度
          if (onStepUpdate) {
            onStepUpdate({
              phase: 'workflow',
              stepIndex: i,
              status: 'in_progress',
              step: step,
              progress: 50
            })
          }
          await this.delay(800)
        }
      } else {
        // 其他顺序任务
        await this.delay(600)

        // 如果有详细信息，逐条显示
        if (step.details) {
          if (step.id === 'schema-extraction' && step.details.fields) {
            // Schema 字段逐个填充
            for (const field of step.details.fields) {
              if (onStepUpdate) {
                onStepUpdate({
                  phase: 'workflow',
                  stepIndex: i,
                  status: 'in_progress',
                  step: step,
                  progressItem: field
                })
              }
              await this.delay(300)
            }
          } else if (step.id === 'query-construction' && step.details.queries) {
            // 查询逐个生成
            for (const query of step.details.queries) {
              if (onStepUpdate) {
                onStepUpdate({
                  phase: 'workflow',
                  stepIndex: i,
                  status: 'in_progress',
                  step: step,
                  progressItem: query
                })
              }
              await this.delay(300)
            }
          } else if (step.id === 'multi-source-pk' && step.details.analysis) {
            // PK分析逐个显示
            for (const analysis of step.details.analysis) {
              if (onStepUpdate) {
                onStepUpdate({
                  phase: 'workflow',
                  stepIndex: i,
                  status: 'in_progress',
                  step: step,
                  progressItem: analysis
                })
              }
              await this.delay(500)
            }
          }
        }
      }

      // 标记步骤完成
      workflowSteps[i].status = 'completed'
      if (onStepUpdate) {
        onStepUpdate({
          phase: 'workflow',
          stepIndex: i,
          status: 'done',
          step: step,
          workflowSteps: [...workflowSteps] // 传递完整的工作流状态
        })
      }
    }

    // 阶段3: 审核报告
    await this.delay(500)
    if (onPhaseChange) {
      onPhaseChange('result')
    }

    if (onStepUpdate) {
      onStepUpdate({
        phase: 'result',
        report: reviewData.finalReport
      })
    }

    // 流式输出回复
    if (onResponse) {
      const responseChunks = this.chunkText(conversation.assistantMessage, 20)
      for (const chunk of responseChunks) {
        await this.delay(50)
        onResponse(chunk)
      }
    }
  }

  /**
   * 获取历史对话列表
   */
  getHistory() {
    if (!this.isEnabled()) {
      throw new Error('Mock mode is not enabled')
    }

    return this.config.history
  }

  /**
   * 获取全局搜索数据
   */
  getGlobalSearchData() {
    if (!this.isEnabled()) {
      throw new Error('Mock mode is not enabled')
    }

    return this.config.globalSearch
  }

  /**
   * 执行搜索
   * @param {string} query - 搜索关键词
   */
  async search(query) {
    if (!this.isEnabled()) {
      throw new Error('Mock mode is not enabled')
    }

    await this.delay(500)

    // 简单的模拟搜索：返回包含查询关键词的结果
    const results = this.config.globalSearch.searchResults.filter(result =>
      result.title.toLowerCase().includes(query.toLowerCase()) ||
      result.excerpt.toLowerCase().includes(query.toLowerCase())
    )

    return results
  }

  /**
   * 获取知识库数据
   */
  getKnowledgeData() {
    if (!this.isEnabled()) {
      throw new Error('Mock mode is not enabled')
    }

    return this.config.knowledge
  }

  /**
   * 按分类获取文档
   * @param {string} categoryId - 分类ID
   */
  getDocumentsByCategory(categoryId) {
    if (!this.isEnabled()) {
      throw new Error('Mock mode is not enabled')
    }

    const category = this.config.knowledge.categories.find(cat => cat.id === categoryId)
    if (!category) return []

    return this.config.knowledge.documents.filter(
      doc => doc.category === category.name
    )
  }

  /**
   * 上传文档到知识库（Mock）
   * @param {File} file - 文件
   * @param {Object} metadata - 元数据
   */
  async uploadDocument(file, metadata) {
    if (!this.isEnabled()) {
      throw new Error('Mock mode is not enabled')
    }

    await this.delay(1500)

    return {
      success: true,
      document: {
        id: `doc-${Date.now()}`,
        title: file.name,
        category: metadata.category,
        size: `${(file.size / 1024 / 1024).toFixed(1)} MB`,
        format: file.name.split('.').pop().toUpperCase(),
        uploadDate: new Date().toISOString().split('T')[0],
        uploadBy: '当前用户',
        status: '待审核',
        tags: metadata.tags || []
      }
    }
  }

  /**
   * 删除文档（Mock）
   * @param {string} docId - 文档ID
   */
  async deleteDocument(docId) {
    if (!this.isEnabled()) {
      throw new Error('Mock mode is not enabled')
    }

    await this.delay(300)

    return {
      success: true,
      message: '文档删除成功（Mock）'
    }
  }

  // 辅助方法：延迟
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  // 辅助方法：将文本分块
  chunkText(text, chunkSize) {
    const chunks = []
    for (let i = 0; i < text.length; i += chunkSize) {
      chunks.push(text.slice(i, i + chunkSize))
    }
    return chunks
  }
}

// 导出单例
export default new MockService()
