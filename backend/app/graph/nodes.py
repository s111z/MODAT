from typing import Dict, Any
from .state import AgentState

# 导入DeepSeek客户端和搜索客户端
try:
    from app.core.llm import deepseek_client
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False

try:
    from app.core.search import search_client
    SEARCH_AVAILABLE = True
except Exception:
    SEARCH_AVAILABLE = False

def node_parse_doc(state) -> Dict[str, Any]:
    """解析上传的PDF文档"""
    state["steps"].append("正在解析文档...")
    
    try:
        # PDF解析
        file_path = state.get("files")[0]
        state["documents"] = [extract_text_from_pdf(file_path)]

        if state.get("documents"):
            state["steps"].append(f"已解析 {len(state['documents'])} 个文档")
        else:
            state["steps"].append("警告: 未找到待解析文档")
            
        return state
    except Exception as e:
        state["steps"].append(f"文档解析失败: {str(e)}")
        raise

def node_search_web(state: AgentState) -> Dict[str, Any]:
    """使用DuckDuckGo进行网络搜索"""
    state["steps"].append("正在使用DuckDuckGo搜索网络资源...")
    
    try:
        query = state.get("query", "")
        if not query:
            state["steps"].append("警告: 未提供搜索查询")
            return state
        
        # 使用DuckDuckGo搜索
        if SEARCH_AVAILABLE:
            try:
                state["steps"].append(f"搜索查询: {query}")
                results = search_client.search(query, max_results=5)
                
                if results:
                    state["web_results"] = results
                    state["steps"].append(f"找到 {len(results)} 条搜索结果")
                else:
                    state["steps"].append("未找到相关搜索结果")
                    state["web_results"] = []
                    
            except Exception as e:
                state["steps"].append(f"DuckDuckGo搜索失败，使用模拟模式: {str(e)}")
                # 降级到模拟模式
                state["web_results"] = [{
                    "title": "模拟搜索结果",
                    "url": "https://example.com",
                    "content": "这是模拟的网络搜索结果内容",
                    "source": "mock"
                }]
        else:
            # 模拟模式
            state["steps"].append("搜索引擎未配置，使用模拟模式")
            state["web_results"] = [{
                "title": "模拟搜索结果",
                "url": "https://example.com",
                "content": "这是模拟的网络搜索结果内容",
                "source": "mock"
            }]
        
        return state
    except Exception as e:
        state["steps"].append(f"网络搜索失败: {str(e)}")
        raise

def node_rag_search(state: AgentState) -> Dict[str, Any]:
    """查询ChromaDB向量数据库"""
    state["steps"].append("正在检索内部知识库...")
    
    try:
        # 模拟RAG搜索 - 实际实现需要ChromaDB
        if "query" not in state:
            state["steps"].append("警告: 未提供检索查询")
            return state
            
        # 搜索前3个相关片段
        results = db_manager.search(query, top_k=3)
        # 拼装上下文
        context = "\n".join([item["content"] for item in results])


        state["steps"].append(f"模拟RAG检索: {state['query']}")
        state["rag_results"] = [{
            "document": "内部文档示例",
            "content": "这是模拟的内部知识库检索结果",
            "score": 0.95
        }]
        
        return state
    except Exception as e:
        state["steps"].append(f"RAG检索失败: {str(e)}")
        raise

def node_conflict_resolution(state: AgentState) -> Dict[str, Any]:
    """模拟多源信息裁决节点"""
    state["steps"].append("正在分析多源信息差异...")
    
    try:
        # 比较网络搜索和RAG搜索结果
        web_results = state.get("web_results", [])
        rag_results = state.get("rag_results", [])
        context_parts = []
        if web_results:
            web_content = "\n".join([
                f"- {r.get('title', '无标题')}: {r.get('content', '')}"
                for r in web_results[:3]  # 最多取3条
            ])
            context_parts.append(f"网络搜索结果:\n{web_content}")
        
        if rag_results:
            rag_content = "\n".join([
                f"- {r.get('document', '文档')}: {r.get('content', '')}"
                for r in rag_results[:3]  # 最多取3条
            ])
            context_parts.append(f"内部知识库结果:\n{rag_content}")

        if web_results and rag_results:
            state["steps"].append("检测到多源信息，正在进行一致性分析...")
            # 模拟冲突解决逻辑
            state["conflict_analysis"] = {
                "web_count": len(web_results),
                "rag_count": len(rag_results),
                "recommendation": "综合两种来源的信息"
            }
            state["steps"].append("已完成冲突分析")
        elif web_results:
            state["steps"].append("仅使用网络搜索结果")
        elif rag_results:
            state["steps"].append("仅使用内部知识库结果")
        else:
            state["steps"].append("警告: 未找到任何搜索结果")
        
        return state
    except Exception as e:
        state["steps"].append(f"冲突解决失败: {str(e)}")
        raise

def node_generate_response(state: AgentState) -> Dict[str, Any]:
    """调用DeepSeek LLM生成最终响应"""
    state["steps"].append("正在调用DeepSeek生成回复...")
    
    try:
        messages = state.get("messages", [])
        web_results = state.get("web_results", [])
        rag_results = state.get("rag_results", [])
        ruling_results = state.get("ruling_results", {})
        query = state.get("query", "")
        
        # 构建上下文信息
        context_parts = []
        
        if web_results:
            web_content = "\n".join([
                f"- {r.get('title', '无标题')}: {r.get('content', '')}"
                for r in web_results[:3]  # 最多取3条
            ])
            context_parts.append(f"网络搜索结果:\n{web_content}")
        
        if rag_results:
            rag_content = "\n".join([
                f"- {r.get('document', '文档')}: {r.get('content', '')}"
                for r in rag_results[:3]  # 最多取3条
            ])
            context_parts.append(f"内部知识库结果:\n{rag_content}")
        
        if ruling_results:
            ruling_content = "\n".join(
                [f"- {r}: {ruling_results[r]}"]
                for r in ruling_results
            )
            context_parts.append(f"冲突分析:\n{ruling_content}")
        
        context = "\n\n".join(context_parts) if context_parts else "无额外上下文信息"
        
        # 使用DeepSeek生成回复
        if LLM_AVAILABLE:
            try:
                system_message = "你是一个专业的文档评审和问答助手。请根据提供的上下文信息，给出准确、有用的回复。"
                response = deepseek_client.generate_response(
                    prompt=query or messages[-1] if messages else "请提供帮助",
                    context=context,
                    system_message=system_message
                )
                state["response"] = response
                state["steps"].append("已使用DeepSeek生成回复")
            except Exception as e:
                state["steps"].append(f"DeepSeek调用失败，使用模拟模式: {str(e)}")
                # 降级到模拟模式
                response = f"基于{'、'.join([p.split(':')[0] for p in context_parts]) if context_parts else '当前上下文'}，这是系统生成的回复。"
                state["response"] = response
        else:
            # 模拟模式
            state["steps"].append("DeepSeek未配置，使用模拟模式")
            response = f"基于{'、'.join([p.split(':')[0] for p in context_parts]) if context_parts else '当前上下文'}，这是系统生成的回复。"
            state["response"] = response
        
        return state
    except Exception as e:
        state["steps"].append(f"响应生成失败: {str(e)}")
        raise