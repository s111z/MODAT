/**
 * 知识问答场景Mock工具函数
 */

/**
 * 流式输出文本
 * @param {String} text - 要输出的完整文本
 * @param {Function} callback - 每次输出字符时的回调函数，参数为当前累积的文本
 * @param {Number} charsPerSecond - 每秒输出的字符数，默认20
 * @returns {Promise} - 返回Promise，可用于取消
 */
export function streamText(text, callback, charsPerSecond = 20) {
  return new Promise((resolve, reject) => {
    const charInterval = 1000 / charsPerSecond; // 每个字符的间隔时间（毫秒）
    let currentIndex = 0;
    let accumulatedText = '';
    let cancelled = false;

    const timer = setInterval(() => {
      if (cancelled) {
        clearInterval(timer);
        reject(new Error('Stream cancelled'));
        return;
      }

      if (currentIndex >= text.length) {
        clearInterval(timer);
        resolve();
        return;
      }

      // 处理多字节字符（中文、emoji等）
      const char = text[currentIndex];
      accumulatedText += char;
      currentIndex++;

      callback(accumulatedText);
    }, charInterval);

    // 返回一个可以取消的对象
    return {
      cancel: () => {
        cancelled = true;
      },
      promise: new Promise((res, rej) => {
        const checkComplete = setInterval(() => {
          if (cancelled) {
            clearInterval(checkComplete);
            rej(new Error('Stream cancelled'));
          } else if (currentIndex >= text.length) {
            clearInterval(checkComplete);
            res();
          }
        }, 100);
      })
    };
  });
}

/**
 * 执行Agent工作流步骤
 * @param {Array} steps - 工作流步骤数组
 * @param {Object} stepDelays - 每个步骤的延迟时间配置
 * @param {Function} onStepStart - 步骤开始时的回调
 * @param {Function} onStepComplete - 步骤完成时的回调
 * @returns {Promise}
 */
export async function executeAgentWorkflow(steps, stepDelays, onStepStart, onStepComplete) {
  for (let i = 0; i < steps.length; i++) {
    const step = steps[i];

    // 触发步骤开始
    if (onStepStart) {
      onStepStart(step, i);
    }

    // 等待步骤执行延迟
    const delayKey = getDelayKey(step.id);
    const delay = stepDelays[delayKey] || 800;
    await sleep(delay);

    // 触发步骤完成
    if (onStepComplete) {
      onStepComplete(step, i);
    }
  }
}

/**
 * 根据步骤ID获取延迟配置的key
 */
function getDelayKey(stepId) {
  const keyMap = {
    'query-analysis': 'queryAnalysis',
    'query-construction': 'queryConstruction',
    'knowledge-retrieval': 'knowledgeRetrieval',
    'web-retrieval': 'webRetrieval',
    'multi-source-pk': 'multiSourcePK',
    'response-generation': 'responseGeneration'
  };
  return keyMap[stepId] || 'default';
}

/**
 * 模拟知识问答完整流程
 * @param {Object} conversationData - 对话数据
 * @param {Object} config - 配置对象
 * @param {Function} onWorkflowUpdate - 工作流更新回调
 * @param {Function} onMessageStream - 消息流式输出回调
 * @returns {Promise}
 */
export async function simulateKnowledgeQA(conversationData, config, onWorkflowUpdate, onMessageStream) {
  // 1. 执行工作流步骤
  const steps = conversationData.agentWorkflow.steps;
  const workflowSteps = steps.map(step => ({
    ...step,
    status: 'pending',
    expanded: false
  }));

  // 更新初始状态
  if (onWorkflowUpdate) {
    onWorkflowUpdate(workflowSteps);
  }

  // 2. 逐步执行工作流
  await executeAgentWorkflow(
    workflowSteps,
    config.agentWorkflow.stepDelays,
    (step, index) => {
      // 步骤开始：设置为processing
      workflowSteps[index].status = 'processing';
      if (onWorkflowUpdate) {
        onWorkflowUpdate([...workflowSteps]);
      }
    },
    (step, index) => {
      // 步骤完成：设置为completed
      workflowSteps[index].status = 'completed';
      if (onWorkflowUpdate) {
        onWorkflowUpdate([...workflowSteps]);
      }
    }
  );

  // 3. 流式输出回复
  if (onMessageStream && config.streamConfig.enabled) {
    await streamText(
      conversationData.assistantMessage,
      (text) => {
        onMessageStream(text);
      },
      config.streamConfig.charsPerSecond
    );
  } else if (onMessageStream) {
    // 如果不启用流式输出，直接返回完整文本
    onMessageStream(conversationData.assistantMessage);
  }
}

/**
 * 辅助函数：延迟执行
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 加载知识问答Mock数据
 * @returns {Promise<Object>}
 */
export async function loadKnowledgeQAData() {
  try {
    const data = await import('./knowledgeQA.json');
    return data.default || data;
  } catch (error) {
    console.error('Failed to load knowledge QA data:', error);
    return null;
  }
}

/**
 * 根据用户消息匹配对话数据
 * @param {String} userMessage - 用户消息
 * @param {Array} conversations - 对话数据列表
 * @returns {Object|null}
 */
export function matchConversation(userMessage, conversations) {
  // 简单的关键词匹配
  for (const conv of conversations) {
    // 精确匹配
    if (conv.userMessage === userMessage) {
      return conv;
    }
  }

  // 如果没有精确匹配，返回第一个作为默认
  return conversations[0] || null;
}

/**
 * 创建知识问答Mock处理器
 * @param {Object} config - 配置对象
 * @returns {Object} - 返回处理器对象
 */
export function createKnowledgeQAHandler(config) {
  let currentStream = null;
  let currentWorkflow = null;

  return {
    /**
     * 处理用户消息
     * @param {String} userMessage - 用户消息
     * @param {Object} callbacks - 回调函数集合
     * @returns {Promise}
     */
    async handleMessage(userMessage, callbacks) {
      const { onWorkflowUpdate, onMessageStream, onComplete } = callbacks;

      // 匹配对话数据
      const conversation = matchConversation(userMessage, config.conversations);
      if (!conversation) {
        console.error('No matching conversation found');
        return;
      }

      // 执行模拟流程
      try {
        await simulateKnowledgeQA(
          conversation,
          config,
          onWorkflowUpdate,
          onMessageStream
        );

        if (onComplete) {
          onComplete();
        }
      } catch (error) {
        console.error('Error in knowledge QA simulation:', error);
      }
    },

    /**
     * 取消当前流程
     */
    cancel() {
      if (currentStream && currentStream.cancel) {
        currentStream.cancel();
      }
    },

    /**
     * 重置状态
     */
    reset() {
      this.cancel();
      currentStream = null;
      currentWorkflow = null;
    }
  };
}

export default {
  streamText,
  executeAgentWorkflow,
  simulateKnowledgeQA,
  loadKnowledgeQAData,
  matchConversation,
  createKnowledgeQAHandler
};
