from typing import List, Dict, Any, Optional
import httpx
from .config import settings
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

class DeepSeekClient:
    """DeepSeek API客户端"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or settings.deepseek_api_key
        self.api_base = api_base or settings.deepseek_api_base
        self.model = model or settings.deepseek_model
        
        if not self.api_key:
            raise ValueError("DeepSeek API密钥未配置")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        调用DeepSeek聊天补全API
        
        Args:
            messages: 对话消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式返回
            
        Returns:
            API响应结果
        """
        url = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers=headers,
                timeout=settings.deepseek_timeout
            )
            response.raise_for_status()
            return response.json()
    
    def generate_response(
        self,
        prompt: str,
        context: Optional[str] = None,
        system_message: Optional[str] = None
    ) -> str:
        """
        生成回复的同步包装方法

        Args:
            prompt: 用户提示
            context: 上下文信息
            system_message: 系统消息

        Returns:
            生成的回复文本
        """
        messages = []

        # 添加系统消息
        if system_message:
            messages.append({
                "role": "system",
                "content": system_message
            })

        # 添加上下文
        if context:
            messages.append({
                "role": "user",
                "content": f"上下文信息：\n{context}\n\n用户问题：{prompt}"
            })
        else:
            messages.append({
                "role": "user",
                "content": prompt
            })

        # 在新线程中运行异步代码，避免事件循环冲突
        def run_in_thread():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(
                    self.chat_completion(messages)
                )
            finally:
                new_loop.close()

        with ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            result = future.result()

        # 提取回复内容
        if result and "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]

        return "抱歉，无法生成回复"

# 全局DeepSeek客户端实例
deepseek_client = DeepSeekClient()
