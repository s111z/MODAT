from pathlib import Path
import sys
current_file_path = Path(__file__).resolve()
BASE_DIR = current_file_path.parent.parent.parent
base_dir_str = str(BASE_DIR)
print("base dir is " + base_dir_str)
if base_dir_str not in sys.path:
    sys.path.insert(0, base_dir_str)

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import asyncio
import os
import uuid

from graph.workflow import create_workflow
from graph.state import AgentState
from graph.vectordb_workflow import create_vectordb_workflow
from graph.vectordb_state import VectorDBState
from datetime import datetime

app = FastAPI(title="智能文档评审问答系统 API")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js默认端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 请求模型
class ChatRequest(BaseModel):
    message: str
    mode: Optional[str] = "qa"  # "qa" 或 "review"
    
class ChatResponse(BaseModel):
    response: str
    steps: List[str]

class ReviewRequest(BaseModel):
    filename: str # 文件在后端的存储名称
    message: str # 用户输入
    mode: Optional[str] = "review"  # "qa" 或 "review"

UpadateFilePath = os.path.join(base_dir_str, "backend/upload_files") 
KnowledgeFilePath = os.path.join(base_dir_str, "backend/knowledge_files")

@app.get("/")
async def root():
    return {
        "message": "智能文档评审问答系统 API",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """处理聊天请求"""
    try:
        # 初始化状态
        state: AgentState = {
            "messages": [request.message],
            "documents": [],
            "review_status": None,
            "steps": [],
            "current_mode": request.mode,
            "query": request.message
        }
        
        # 创建并执行工作流
        workflow = create_workflow()
        result = workflow.invoke(state)
        
        return ChatResponse(
            response=result.get("response", "抱歉，未能生成回复"),
            steps=result.get("steps", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """流式处理聊天请求"""
    async def generate():
        try:
            # 初始化状态
            state: AgentState = {
                "messages": [request.message],
                "documents": [],
                "review_status": None,
                "steps": [],
                "current_mode": request.mode,
                "query": request.message
            }
            
            # 模拟流式输出
            steps = [
                "正在理解您的问题...",
                "正在搜索相关信息...",
                "正在分析数据...",
                "正在生成回复..."
            ]
            
            for step in steps:
                data = json.dumps({"type": "step", "content": step}, ensure_ascii=False)
                yield f"data: {data}\n\n"
                await asyncio.sleep(0.5)
            
            # 创建并执行工作流
            workflow = create_workflow()
            result = workflow.invoke(state)
            
            # 发送最终响应
            response_data = json.dumps({
                "type": "response",
                "content": result.get("response", "抱歉，未能生成回复"),
                "steps": result.get("steps", [])
            }, ensure_ascii=False)
            yield f"data: {response_data}\n\n"
            
        except Exception as e:
            error_data = json.dumps({"type": "error", "content": str(e)}, ensure_ascii=False)
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/api/review")
async def review(request: ReviewRequest):
    """处理方案审核需求"""
    try:
        # 初始化状态
        state: AgentState = {
            "messages": [request.message],
            "filename": [request.filename],
            "documents": [],
            "review_status": None,
            "steps": [],
            "current_mode": request.mode,
            "query": request.message
        }
        
        # 创建并执行工作流
        workflow = create_workflow()
        result = workflow.invoke(state)
        
        return ChatResponse(
            response=result.get("response", "抱歉，未能生成回复"),
            steps=result.get("steps", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """处理文件上传"""
    try:
        # 验证文件类型
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="仅支持PDF文件")
        
        # 读取文件内容
        content = await file.read()
        
        # 存储文件
        file_name = os.path.splitext(file.filename)[0]
        file_ext = os.path.splitext(file.filename)[1]
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_name}_{file_id}{file_ext}"

        file_path = os.path.join(UpadateFilePath, safe_filename)
        # 写入临时文件
        with open(file_path, "wb") as f:
            f.write(content)

        # 将成功状态传到前端    
        return {
            "savefilename": safe_filename,
            "size": len(content),
            "status": "success",
            "message": "文件上传成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}

# ====== 向量库管理 API ======

class VectorDBAddRequest(BaseModel):
    filename: str
    metadatas: Optional[Dict] = None # 只上传文档类别和权限，其他全部为中间数据

class VectorDBSearchRequest(BaseModel):
    query: str
    top_k: int = 3
    filter_meta: Optional[Dict] = None

class VectorDBUpdateRequest(BaseModel):
    ids: List[str]
    texts: List[str]
    metadatas: Optional[List[Dict]] = None

class VectorDBDeleteRequest(BaseModel):
    ids: Optional[List[str]] = None
    filter_meta: Optional[Dict] = None

class VectorDBResponse(BaseModel):
    success: bool
    message: str
    results: List[Dict[str, Any]]
    steps: List[str]

@app.post("/api/knowledge_upload")
async def upload_knowledge_file(file: UploadFile = File(...)):
    """处理文件上传"""
    try:
        # 验证文件类型
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="仅支持PDF文件")
        
        # 读取文件内容
        content = await file.read()
        
        # 存储文件
        file_name = os.path.splitext(file.filename)[0]
        file_ext = os.path.splitext(file.filename)[1]
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_name}_{file_id}{file_ext}"

        file_path = os.path.join(KnowledgeFilePath, safe_filename)
        # 写入临时文件
        with open(file_path, "wb") as f:
            f.write(content)

        # 将成功状态传到前端    
        return {
            "savefilename": safe_filename,
            "size": len(content),
            "status": "success",
            "message": "文件上传成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# fixing    
@app.post("/api/vectordb/add", response_model=VectorDBResponse)
async def add_documents(request: VectorDBAddRequest):
    """添加文档到向量库"""
    try:
        category = request.metadatas.get("category", "law")
        permissions = request.metadatas.get("permissions", 0) # 0表示公共文档，判断权限用大于等于
        source = os.path.join(KnowledgeFilePath, request.filename)
        file_type = os.path.splitext(request.filename)[1]
        create_at = datetime.now()
        print(f"source is {source}, file_type is {file_type}")

        state: VectorDBState = {
            "operation": "add",
            "filename": request.filename,
            "content": "",
            "file_id": "",
            "source": source,
            "file_type": file_type,
            "chunk_index": 0,
            "total_chunks": 0,
            "create_at": create_at,
            "category": category,
            "permissions": permissions,
            "results": [],
            "success": False,
            "message": "",
            "steps": []
        }
        
        workflow = create_vectordb_workflow()
        result = workflow.invoke(state)
        
        return VectorDBResponse(
            success=result["success"],
            message=result["message"],
            results=result["results"],
            steps=result["steps"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vectordb/search", response_model=VectorDBResponse)
async def search_documents(request: VectorDBSearchRequest):
    """搜索向量库"""
    try:
        state: VectorDBState = {
            "operation": "search",
            "filename": "",
            "content": "",
            "file_id": "",
            "source": None,
            "file_type": None,
            "chunk_index": 0,
            "total_chunks": 0,
            "create_at": None,
            "category": None,
            "permissions": 0,
            "query": request.query,
            "top_k": request.top_k,
            "filter_meta": request.filter_meta,
            "results": [],
            "success": False,
            "message": "",
            "steps": []
        }
        
        workflow = create_vectordb_workflow()
        result = workflow.invoke(state)
        
        return VectorDBResponse(
            success=result["success"],
            message=result["message"],
            results=result["results"],
            steps=result["steps"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vectordb/update", response_model=VectorDBResponse)
async def update_documents(request: VectorDBUpdateRequest):
    """更新向量库中的文档"""
    try:
        state: VectorDBState = {
            "operation": "update",
            "texts": request.texts,
            "metadatas": request.metadatas,
            "ids": request.ids,
            "query": None,
            "top_k": 3,
            "filter_meta": None,
            "results": [],
            "success": False,
            "message": "",
            "steps": []
        }
        
        workflow = create_vectordb_workflow()
        result = workflow.invoke(state)
        
        return VectorDBResponse(
            success=result["success"],
            message=result["message"],
            results=result["results"],
            steps=result["steps"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/vectordb/delete", response_model=VectorDBResponse)
async def delete_documents(request: VectorDBDeleteRequest):
    """删除向量库中的文档"""
    try:
        if not request.ids and not request.filter_meta:
            raise HTTPException(
                status_code=400,
                detail="必须提供文档ID列表或过滤条件"
            )
        
        state: VectorDBState = {
            "operation": "delete",
            "texts": [],
            "metadatas": None,
            "ids": request.ids,
            "query": None,
            "top_k": 3,
            "filter_meta": request.filter_meta,
            "results": [],
            "success": False,
            "message": "",
            "steps": []
        }
        
        workflow = create_vectordb_workflow()
        result = workflow.invoke(state)
        
        return VectorDBResponse(
            success=result["success"],
            message=result["message"],
            results=result["results"],
            steps=result["steps"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/vectordb/list", response_model=VectorDBResponse)
async def list_documents(limit: int = 10):
    """列出向量库中的文档"""
    try:
        state: VectorDBState = {
            "operation": "get_all",
            "texts": [],
            "metadatas": None,
            "ids": None,
            "query": None,
            "top_k": limit,
            "filter_meta": None,
            "results": [],
            "success": False,
            "message": "",
            "steps": []
        }
        
        workflow = create_vectordb_workflow()
        result = workflow.invoke(state)
        
        return VectorDBResponse(
            success=result["success"],
            message=result["message"],
            results=result["results"],
            steps=result["steps"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=6006)