from typing import Dict, Any
from .vectordb_state import VectorDBState
from core.vector_store import db_manager
from core.text_splitter import RecursiveCharacterTextSplitter
from core.parse_doc import extract_text_from_pdf
import uuid

def node_generate_response(state: VectorDBState) -> Dict[str, Any]:
    """调用DeepSeek LLM生成最终响应"""
    state["steps"].append("正在调用DeepSeek生成回复...")
    
    try:
        search_result = state.get("results", [])
        # web_results = state.get("web_results", [])
        # rag_results = state.get("rag_results", [])
        # ruling_results = state.get("ruling_results", {})
        query = state.get("query", "")
        
        # 构建上下文信息
        context_parts = []
        for item in search_result:
            context_parts.append(item["content"])
        # if web_results:
        #     web_content = "\n".join([
        #         f"- {r.get('title', '无标题')}: {r.get('content', '')}"
        #         for r in web_results[:3]  # 最多取3条
        #     ])
        #     context_parts.append(f"网络搜索结果:\n{web_content}")
        
        # if rag_results:
        #     rag_content = "\n".join([
        #         f"- {r.get('document', '文档')}: {r.get('content', '')}"
        #         for r in rag_results[:3]  # 最多取3条
        #     ])
        #     context_parts.append(f"内部知识库结果:\n{rag_content}")
        
        # if ruling_results:
        #     ruling_content = "\n".join(
        #         [f"- {r}: {ruling_results[r]}"]
        #         for r in ruling_results
        #     )
        #     context_parts.append(f"冲突分析:\n{ruling_content}")
        
        context = "\n\n".join(context_parts) if context_parts else "无额外上下文信息"
        
        # 使用DeepSeek生成回复
        if LLM_AVAILABLE:
            try:
                system_message = "你是一个专业的问答助手。请根据提供的上下文信息，给出准确、有用的回复。回复一定要基于上下文，尽量不要自行拓展"
                response = deepseek_client.generate_response(
                    prompt=query, 
                    context=context,
                    system_message=system_message
                )
                state["answer"] = response
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

def node_search_documents(state: VectorDBState) -> Dict[str, Any]:
    """搜索向量库
    
    根据查询字符串进行语义搜索，返回最相关的文档
    """
    state["steps"].append("正在搜索向量库...")
    
    try:
        query = state.get("query")
        if not query:
            state["success"] = False
            state["message"] = "错误：未提供搜索查询"
            state["steps"].append(state["message"])
            return state
        
        top_k = state.get("top_k", 3)
        filter_meta = state.get("filter_meta")
        
        # 调用 VectorDBManager 搜索
        results = db_manager.search(
            query=query,
            top_k=top_k,
            filter_meta=filter_meta
        )
        
        state["results"] = results
        state["success"] = True
        state["message"] = f"找到 {len(results)} 条相关文档"
        state["steps"].append(state["message"])
        
        return state
        
    except Exception as e:
        state["success"] = False
        state["message"] = f"搜索失败: {str(e)}"
        state["steps"].append(state["message"])
        return state

def node_update_document(state: VectorDBState) -> Dict[str, Any]:
    """更新向量库中的文档
    
    根据文档ID更新文本内容和元数据
    """
    state["steps"].append("正在更新文档...")
    
    try:
        ids = state.get("ids", [])
        texts = state.get("texts", [])
        metadatas = state.get("metadatas")
        
        if not ids or not texts:
            state["success"] = False
            state["message"] = "错误：必须提供文档ID和新文本"
            state["steps"].append(state["message"])
            return state
        
        if len(ids) != len(texts):
            state["success"] = False
            state["message"] = f"错误：ID数量({len(ids)})与文本数量({len(texts)})不匹配"
            state["steps"].append(state["message"])
            return state
        
        # 批量更新
        success_count = 0
        failed_ids = []
        
        for i, doc_id in enumerate(ids):
            new_text = texts[i]
            new_metadata = metadatas[i] if metadatas and i < len(metadatas) else None
            
            if db_manager.update_text(doc_id, new_text, new_metadata):
                success_count += 1
            else:
                failed_ids.append(doc_id)
        
        state["results"] = [{
            "updated_count": success_count,
            "total_count": len(ids),
            "failed_ids": failed_ids
        }]
        state["success"] = success_count > 0
        state["message"] = f"成功更新 {success_count}/{len(ids)} 条文档"
        
        if failed_ids:
            state["message"] += f"，失败的ID: {failed_ids}"
        
        state["steps"].append(state["message"])
        return state
        
    except Exception as e:
        state["success"] = False
        state["message"] = f"更新文档失败: {str(e)}"
        state["steps"].append(state["message"])
        return state

def node_delete_documents(state: VectorDBState) -> Dict[str, Any]:
    """删除向量库中的文档
    
    支持按ID列表删除或按元数据条件删除
    """
    state["steps"].append("正在删除文档...")
    
    try:
        ids = state.get("ids")
        filter_meta = state.get("filter_meta")
        
        if ids:
            # 按ID删除
            db_manager.delete_by_ids(ids)
            state["results"] = [{"deleted_ids": ids, "count": len(ids)}]
            state["message"] = f"成功删除 {len(ids)} 条文档"
        elif filter_meta:
            # 按条件删除
            db_manager.delete_by_filter(filter_meta)
            state["results"] = [{"filter": filter_meta}]
            state["message"] = "成功按条件删除文档"
        else:
            state["success"] = False
            state["message"] = "错误：必须提供文档ID列表或过滤条件"
            state["steps"].append(state["message"])
            return state
        
        state["success"] = True
        state["steps"].append(state["message"])
        return state
        
    except Exception as e:
        state["success"] = False
        state["message"] = f"删除文档失败: {str(e)}"
        state["steps"].append(state["message"])
        return state

def node_get_all_documents(state: VectorDBState) -> Dict[str, Any]:
    """获取所有文档（用于调试和管理）
    
    返回向量库中的文档列表，数量由 top_k 限制
    """
    state["steps"].append("正在获取文档列表...")
    
    try:
        limit = state.get("top_k", 10)
        results = db_manager.get_all(limit=limit)
        
        state["results"] = results
        state["success"] = True
        state["message"] = f"获取到 {len(results)} 条文档"
        state["steps"].append(state["message"])
        
        return state
        
    except Exception as e:
        state["success"] = False
        state["message"] = f"获取文档失败: {str(e)}"
        state["steps"].append(state["message"])
        return state


def node_add_documents(state: VectorDBState) -> Dict[str, Any]:
    """解析并切分文档节点

    1. 从文件路径读取文档内容（支持PDF等格式）
    2. 使用文本切分器将文档切分成chunks
    3. 将切分后的chunks添加到向量库
    4. 返回切分结果和存储状态
    """
    state["steps"].append("正在解析文档...")

    try:
        # 获取文件路径
        filepath = state.get("source")
        if not filepath:
            state["success"] = False
            state["message"] = "错误：未提供文件路径"
            state["steps"].append(state["message"])
            return state

        # 根据文件类型解析文档
        file_type = state.get("file_type", "").lower()
        filename = state.get("filename")
        state["steps"].append(f"正在读取文件: {filename}")

        # 解析PDF文件
        if file_type == '.pdf':
            try:
                text = extract_text_from_pdf(filepath)
                state["content"] = text
                state["steps"].append(f"成功提取PDF文本，共 {len(text)} 个字符")
            except Exception as e:
                state["success"] = False
                state["message"] = f"PDF解析失败: {str(e)}"
                state["steps"].append(state["message"])
                return state
        else:
            # 处理纯文本文件
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    text = f.read()
                state["content"] = text
                state["steps"].append(f"成功读取文本文件，共 {len(text)} 个字符")
            except Exception as e:
                state["success"] = False
                state["message"] = f"文件读取失败: {str(e)}"
                state["steps"].append(state["message"])
                return state

        # 检查文本是否为空
        if not text or len(text.strip()) == 0:
            state["success"] = False
            state["message"] = "错误：文档内容为空"
            state["steps"].append(state["message"])
            return state

        # 切分文档
        state["steps"].append("正在切分文档...")

        # 获取切分参数
        chunk_size = state.get("chunk_size", 2000)
        chunk_overlap = state.get("chunk_overlap", 100)

        # 使用递归字符切分器
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        # 切分文本
        chunks = splitter.split_text(text)

        state["steps"].append(f"文档切分完成，共 {len(chunks)} 个chunks")

        # 准备元数据
        base_metadata = {
            "source": state.get("source"),
            "file_type": file_type or filename.split('.')[-1],
            "created_at": state.get("created_at", ""),
            "category": state.get("category", ""),
            "permissions": state.get("permissions", 0)
        }

        # 为每个chunk添加元数据
        metadatas = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                **base_metadata,
                "file_id": str(uuid.uuid4()),
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
            metadatas.append(chunk_metadata)

        # 将切分后的文档添加到向量库
        state["steps"].append("正在将chunks添加到向量库...")

        try:
            result_ids = db_manager.add_texts(
                texts=chunks,
                metadatas=metadatas
            )

            if result_ids:
                state["results"] = [{
                    "ids": result_ids,
                    "chunk_count": len(chunks),
                    "total_chars": len(text),
                    "avg_chunk_size": len(text) // len(chunks) if chunks else 0
                }]
                state["success"] = True
                state["message"] = f"成功解析并存储文档，共 {len(chunks)} 个chunks"
                state["steps"].append(state["message"])
            else:
                state["success"] = False
                state["message"] = "文档切分成功，但存储到向量库失败"
                state["steps"].append(state["message"])

        except Exception as e:
            state["success"] = False
            state["message"] = f"存储到向量库失败: {str(e)}"
            state["steps"].append(state["message"])

        return state

    except Exception as e:
        state["success"] = False
        state["message"] = f"文档解析失败: {str(e)}"
        state["steps"].append(state["message"])
        return state