from pathlib import Path
import sys
current_file_path = Path(__file__).resolve()
BASE_DIR = current_file_path.parent.parent.parent
base_dir_str = str(BASE_DIR)
app_dir_str = str(current_file_path.parent)
print("base dir is " + base_dir_str)
if base_dir_str not in sys.path:
    sys.path.insert(0, base_dir_str)
if app_dir_str not in sys.path:
    sys.path.insert(0, app_dir_str)

from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import asyncio
import os
import uuid
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)

from graph.qa_workflow import create_qa_workflow
from graph.qa_state import QAState
from graph.review_workflow import create_review_workflow
from graph.review_state import ReviewState
from graph.vectordb_workflow import create_vectordb_workflow
from graph.vectordb_state import VectorDBState
from session.session_store import session_store
from api.websocket_handler import ws_manager
from task.task_queue import task_queue
from task.task_models import Task, TaskStatus, TaskType
from core.vector_store import db_manager
from datetime import datetime

app = FastAPI(title="智能文档评审问答系统 API")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====== 请求/响应模型 ======

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    mode: Optional[str] = "qa"  # "qa" 或 "review"

class ChatResponse(BaseModel):
    response: str
    steps: List[str]
    session_id: str

class ReviewRequest(BaseModel):
    filename: str
    message: str
    session_id: Optional[str] = None
    mode: Optional[str] = "review"

UpadateFilePath = os.path.join(base_dir_str, "backend/upload_files")
KnowledgeFilePath = os.path.join(base_dir_str, "backend/knowledge_files")

# ====== 核心 API ======

@app.get("/")
async def root():
    return {
        "message": "智能文档评审问答系统 API",
        "version": "2.0.0",
        "status": "running"
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """处理聊天请求（使用新QA工作流）"""
    try:
        # 生成或复用session_id
        sid = request.session_id or str(uuid.uuid4())

        # 获取对话历史
        history = session_store.build_context(sid)

        # 初始化QA工作流状态
        state: QAState = {
            "query": request.message,
            "session_id": sid,
            "desensitized_query": "",
            "pii_mapping": {},
            "intent": "",
            "deep_mode": False,
            "processed_queries": [],
            "query_type": "simple",
            "knowledge_results": [],
            "web_results": [],
            "resolved_context": "",
            "conflict_found": False,
            "conflict_summary": "",
            "history": history,
            "response": "",
            "steps": [],
        }

        # 创建并执行工作流
        workflow = create_qa_workflow()
        result = workflow.invoke(state)

        response_text = result.get("response", "抱歉，未能生成回复")

        # 保存到会话历史
        session_store.add_message(sid, "user", request.message)
        session_store.add_message(sid, "assistant", response_text)

        return ChatResponse(
            response=response_text,
            steps=result.get("steps", []),
            session_id=sid,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """流式处理聊天请求"""
    async def generate():
        try:
            sid = request.session_id or str(uuid.uuid4())
            history = session_store.build_context(sid)

            state: QAState = {
                "query": request.message,
                "session_id": sid,
                "desensitized_query": "",
                "pii_mapping": {},
                "intent": "",
                "deep_mode": False,
                "processed_queries": [],
                "query_type": "simple",
                "knowledge_results": [],
                "web_results": [],
                "resolved_context": "",
                "conflict_found": False,
                "conflict_summary": "",
                "history": history,
                "response": "",
                "steps": [],
            }

            # 发送session_id
            meta = json.dumps({"type": "meta", "session_id": sid}, ensure_ascii=False)
            yield f"data: {meta}\n\n"

            # 执行工作流
            workflow = create_qa_workflow()
            result = workflow.invoke(state)

            # 逐条发送步骤
            for step in result.get("steps", []):
                data = json.dumps({"type": "step", "content": step}, ensure_ascii=False)
                yield f"data: {data}\n\n"
                await asyncio.sleep(0.1)

            response_text = result.get("response", "抱歉，未能生成回复")

            # 保存会话
            session_store.add_message(sid, "user", request.message)
            session_store.add_message(sid, "assistant", response_text)

            # 发送最终响应
            response_data = json.dumps({
                "type": "response",
                "content": response_text,
                "steps": result.get("steps", []),
                "session_id": sid,
            }, ensure_ascii=False)
            yield f"data: {response_data}\n\n"

        except Exception as e:
            error_data = json.dumps({"type": "error", "content": str(e)}, ensure_ascii=False)
            yield f"data: {error_data}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/api/review")
async def review(request: ReviewRequest):
    """处理方案审核需求（使用审核工作流）"""
    try:
        sid = request.session_id or str(uuid.uuid4())

        # 构造文件路径
        filepath = os.path.join(UpadateFilePath, request.filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail=f"文件不存在: {request.filename}")

        state: ReviewState = {
            "query": request.message,
            "session_id": sid,
            "filepath": filepath,
            "desensitized_query": "",
            "pii_mapping": {},
            "intent": "document_review",
            "has_history": False,
            "has_policy_change": True,
            "doc_info": {},
            "doc_text": "",
            "structured_data": {},
            "review_queries": [],
            "review_dimensions": [],
            "knowledge_results": [],
            "web_results": [],
            "resolved_context": "",
            "conflict_found": False,
            "conflict_summary": "",
            "inquiry_result": {},
            "rewrite_suggestions": "",
            "review_report": "",
            "response": "",
            "steps": [],
        }

        workflow = create_review_workflow()
        result = workflow.invoke(state)

        response_text = result.get("response", "抱歉，未能生成回复")
        session_store.add_message(sid, "user", request.message)
        session_store.add_message(sid, "assistant", response_text)

        return ChatResponse(
            response=response_text,
            steps=result.get("steps", []),
            session_id=sid,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ====== 文件上传 API ======

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt'}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """处理方案文件上传"""
    try:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"仅支持 {', '.join(ALLOWED_EXTENSIONS)} 格式")

        content = await file.read()
        file_name = os.path.splitext(file.filename)[0]
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_name}_{file_id}{ext}"

        file_path = os.path.join(UpadateFilePath, safe_filename)
        with open(file_path, "wb") as f:
            f.write(content)

        return {
            "savefilename": safe_filename,
            "size": len(content),
            "status": "success",
            "message": "文件上传成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/knowledge_upload")
async def upload_knowledge_file(file: UploadFile = File(...)):
    """处理知识库文件上传"""
    try:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"仅支持 {', '.join(ALLOWED_EXTENSIONS)} 格式")

        content = await file.read()
        file_name = os.path.splitext(file.filename)[0]
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_name}_{file_id}{ext}"

        file_path = os.path.join(KnowledgeFilePath, safe_filename)
        with open(file_path, "wb") as f:
            f.write(content)

        return {
            "savefilename": safe_filename,
            "size": len(content),
            "status": "success",
            "message": "文件上传成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ====== 健康检查 ======

@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "version": "2.0.0"}

# ====== WebSocket API ======

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket连接，用于实时推送Agent执行步骤"""
    await ws_manager.connect(session_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif msg_type == "chat":
                # 通过WebSocket发起QA请求
                message = data.get("message", "")
                history = session_store.build_context(session_id)

                state: QAState = {
                    "query": message,
                    "session_id": session_id,
                    "desensitized_query": "",
                    "pii_mapping": {},
                    "intent": "",
                    "deep_mode": False,
                    "processed_queries": [],
                    "query_type": "simple",
                    "knowledge_results": [],
                    "web_results": [],
                    "resolved_context": "",
                    "conflict_found": False,
                    "conflict_summary": "",
                    "history": history,
                    "response": "",
                    "steps": [],
                }

                workflow = create_qa_workflow()
                result = workflow.invoke(state)

                # 推送步骤
                for step in result.get("steps", []):
                    await ws_manager.send_step(session_id, step)

                response_text = result.get("response", "抱歉，未能生成回复")
                session_store.add_message(session_id, "user", message)
                session_store.add_message(session_id, "assistant", response_text)

                await ws_manager.send_result(session_id, {
                    "response": response_text,
                    "steps": result.get("steps", []),
                })
    except WebSocketDisconnect:
        ws_manager.disconnect(session_id)

# ====== 任务管理 API ======

@app.post("/api/task/submit")
async def submit_review_task(request: ReviewRequest):
    """提交异步审核任务"""
    try:
        sid = request.session_id or str(uuid.uuid4())
        filepath = os.path.join(UpadateFilePath, request.filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail=f"文件不存在: {request.filename}")

        task = Task(
            task_type=TaskType.REVIEW,
            session_id=sid,
            input_data={
                "message": request.message,
                "filename": request.filename,
                "filepath": filepath,
            },
        )

        await task_queue.submit(task)

        return {
            "task_id": task.task_id,
            "session_id": sid,
            "status": task.status.value,
            "message": "任务已提交",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/task/{task_id}")
async def get_task_status(task_id: str):
    """查询任务状态"""
    task = task_queue.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return {
        "task_id": task.task_id,
        "status": task.status.value,
        "steps": task.steps,
        "result": task.result,
        "error": task.error,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }

@app.get("/api/tasks")
async def list_tasks(session_id: str = None, limit: int = 20):
    """列出任务"""
    tasks = task_queue.list_tasks(session_id=session_id, limit=limit)
    return {
        "tasks": [
            {
                "task_id": t.task_id,
                "task_type": t.task_type.value,
                "status": t.status.value,
                "created_at": t.created_at.isoformat(),
            }
            for t in tasks
        ]
    }

# ====== 向量库管理 API (保留原有功能) ======

class VectorDBAddRequest(BaseModel):
    filename: str
    metadatas: Optional[Dict] = None

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

@app.post("/api/vectordb/add", response_model=VectorDBResponse)
async def add_documents(request: VectorDBAddRequest):
    """添加文档到向量库"""
    try:
        category = request.metadatas.get("category", "law")
        permissions = request.metadatas.get("permissions", 0)
        source = os.path.join(KnowledgeFilePath, request.filename)
        file_type = os.path.splitext(request.filename)[1]
        create_at = datetime.now()

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

@app.post("/api/vectordb/qa", response_model=VectorDBResponse)
async def rag_qa(request: VectorDBSearchRequest):
    """向量库QA"""
    try:
        state: VectorDBState = {
            "operation": "qa",
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
            "top_k": 3,
            "filter_meta": None,
            "results": [],
            "success": False,
            "message": "",
            "steps": [],
            "answer": ""
        }

        workflow = create_vectordb_workflow()
        result = workflow.invoke(state)

        return VectorDBResponse(
            success=result["success"],
            message=result["message"],
            results=[{"answer": result["answer"]}],
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

class BatchImportRequest(BaseModel):
    category: str = "law"
    permissions: int = 0
    subdirs: Optional[List[str]] = None  # 指定子目录, None=扫描全部


@app.post("/api/knowledge/batch_import")
async def batch_import_knowledge(request: BatchImportRequest = BatchImportRequest()):
    """增量同步 knowledge_files/ 目录到向量库。

    - 新文件（目录有、向量库没有）→ 导入
    - 已有文件（目录有、向量库也有）→ 跳过
    - 已删文件（目录没有、向量库有）→ 从向量库删除
    """
    # 1. 扫描磁盘文件
    scan_dirs = []
    if request.subdirs:
        for sub in request.subdirs:
            d = os.path.join(KnowledgeFilePath, sub)
            if os.path.isdir(d):
                scan_dirs.append(d)
    else:
        scan_dirs.append(KnowledgeFilePath)

    supported_exts = {".pdf", ".docx", ".doc", ".txt"}
    disk_files = {}  # filepath -> file_info
    for scan_dir in scan_dirs:
        for root, _dirs, filenames in os.walk(scan_dir):
            for fname in filenames:
                if fname.startswith("."):
                    continue
                ext = os.path.splitext(fname)[1].lower()
                if ext in supported_exts:
                    filepath = os.path.join(root, fname)
                    disk_files[filepath] = {
                        "filename": fname,
                        "filepath": filepath,
                        "ext": ext,
                        "subdir": os.path.relpath(root, KnowledgeFilePath),
                    }

    # 2. 查询向量库中已有的 source 集合
    existing_sources = db_manager.get_all_sources()

    # 3. 计算差异
    disk_paths = set(disk_files.keys())
    to_add = disk_paths - existing_sources       # 新文件：需要导入
    to_skip = disk_paths & existing_sources       # 已有：跳过
    to_delete = existing_sources - disk_paths     # 已删：需要从向量库清理

    results = []
    add_success = 0
    add_fail = 0
    delete_count = 0

    # 4. 删除向量库中已不存在于磁盘的文件
    for source_path in to_delete:
        try:
            db_manager.delete_by_filter({"source": source_path})
            delete_count += 1
            results.append({
                "filename": os.path.basename(source_path),
                "action": "deleted",
                "success": True,
                "message": "文件已从磁盘删除，向量库已同步清理",
            })
        except Exception as e:
            results.append({
                "filename": os.path.basename(source_path),
                "action": "delete_failed",
                "success": False,
                "message": str(e),
            })

    # 5. 跳过已存在的文件
    for filepath in to_skip:
        info = disk_files[filepath]
        results.append({
            "filename": info["filename"],
            "subdir": info["subdir"],
            "action": "skipped",
            "success": True,
            "message": "已在向量库中，跳过",
        })

    # 6. 导入新文件
    for filepath in to_add:
        file_info = disk_files[filepath]
        try:
            subdir = file_info["subdir"]
            state: VectorDBState = {
                "operation": "add",
                "filename": file_info["filename"],
                "content": "",
                "file_id": "",
                "source": filepath,
                "file_type": file_info["ext"],
                "chunk_index": 0,
                "total_chunks": 0,
                "created_at": str(datetime.now()),
                "category": f"{request.category}/{subdir}" if subdir != "." else request.category,
                "permissions": request.permissions,
                "results": [],
                "success": False,
                "message": "",
                "steps": [],
            }

            workflow = create_vectordb_workflow()
            result = workflow.invoke(state)

            results.append({
                "filename": file_info["filename"],
                "subdir": subdir,
                "action": "added",
                "success": result["success"],
                "message": result["message"],
            })

            if result["success"]:
                add_success += 1
            else:
                add_fail += 1

        except Exception as e:
            add_fail += 1
            results.append({
                "filename": file_info["filename"],
                "subdir": file_info["subdir"],
                "action": "add_failed",
                "success": False,
                "message": str(e),
            })

    return {
        "status": "success" if add_fail == 0 else "partial",
        "message": (
            f"同步完成: 新增 {add_success} 个, "
            f"跳过 {len(to_skip)} 个, "
            f"清理 {delete_count} 个, "
            f"失败 {add_fail} 个"
        ),
        "total_on_disk": len(disk_files),
        "added": add_success,
        "skipped": len(to_skip),
        "deleted": delete_count,
        "failed": add_fail,
        "results": results,
    }


@app.get("/api/knowledge/scan")
async def scan_knowledge_files():
    """扫描 knowledge_files/ 目录结构，列出所有可导入文件（不执行导入）"""
    supported_exts = {".pdf", ".docx", ".doc", ".txt"}
    files = []
    for root, _dirs, filenames in os.walk(KnowledgeFilePath):
        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext in supported_exts:
                full_path = os.path.join(root, fname)
                files.append({
                    "filename": fname,
                    "subdir": os.path.relpath(root, KnowledgeFilePath),
                    "ext": ext,
                    "size_kb": round(os.path.getsize(full_path) / 1024, 1),
                })

    return {
        "knowledge_dir": KnowledgeFilePath,
        "total": len(files),
        "files": files,
    }


@app.get("/api/knowledge/tree")
async def knowledge_file_tree():
    """以树形结构返回知识库目录"""
    supported_exts = {".pdf", ".docx", ".doc", ".txt"}
    tree = {}

    for root, _dirs, filenames in os.walk(KnowledgeFilePath):
        rel_dir = os.path.relpath(root, KnowledgeFilePath)
        category = rel_dir if rel_dir != "." else "根目录"

        files_in_dir = []
        for fname in filenames:
            if fname.startswith("."):
                continue
            ext = os.path.splitext(fname)[1].lower()
            if ext in supported_exts:
                full_path = os.path.join(root, fname)
                files_in_dir.append({
                    "filename": fname,
                    "ext": ext,
                    "size_kb": round(os.path.getsize(full_path) / 1024, 1),
                })

        if files_in_dir:
            tree[category] = files_in_dir

    return {"tree": tree}


@app.get("/api/knowledge/download")
async def download_knowledge_file(subdir: str = ".", filename: str = ""):
    """下载知识库文件"""
    if not filename:
        raise HTTPException(status_code=400, detail="缺少文件名")

    # 防止路径穿越攻击
    safe_subdir = os.path.normpath(subdir)
    safe_filename = os.path.basename(filename)

    if ".." in safe_subdir:
        raise HTTPException(status_code=400, detail="非法路径")

    if safe_subdir == ".":
        file_path = os.path.join(KnowledgeFilePath, safe_filename)
    else:
        file_path = os.path.join(KnowledgeFilePath, safe_subdir, safe_filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        path=file_path,
        filename=safe_filename,
        media_type="application/octet-stream"
    )


@app.get("/api/knowledge/preview")
async def preview_knowledge_file(subdir: str = ".", filename: str = ""):
    """预览知识库文件（使用正确的 MIME 类型，浏览器可内联展示 PDF）"""
    if not filename:
        raise HTTPException(status_code=400, detail="缺少文件名")

    safe_subdir = os.path.normpath(subdir)
    safe_filename = os.path.basename(filename)

    if ".." in safe_subdir:
        raise HTTPException(status_code=400, detail="非法路径")

    if safe_subdir == ".":
        file_path = os.path.join(KnowledgeFilePath, safe_filename)
    else:
        file_path = os.path.join(KnowledgeFilePath, safe_subdir, safe_filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    ext = os.path.splitext(safe_filename)[1].lower()
    mime_map = {
        ".pdf": "application/pdf",
        ".txt": "text/plain; charset=utf-8",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    media_type = mime_map.get(ext, "application/octet-stream")

    return FileResponse(
        path=file_path,
        filename=safe_filename,
        media_type=media_type,
        headers={"Content-Disposition": f"inline; filename*=UTF-8''{safe_filename}"}
    )


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
