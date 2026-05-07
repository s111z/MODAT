# MODAT 出海场景下的方案评审和问答系统

MODAT 是一个面向出海场景的方案审核、知识库问答和文档智能分析的全栈项目。系统由 FastAPI 后端、Vue 2 主前端、知识库向量检索、LangGraph 工作流和文档上传/审核流程组成。

当前项目中存在两个前端实现：

- `frontend-vue2/`：当前更完整的主前端，包含首页入口、方案审核、智能问询、知识库管理等页面。
- `frontend/`：不知道有什么用后面或许要删掉。

---

## 1. 快速启动

以下命令默认从项目根目录 `MODAT/` 开始。

### 1.1 启动后端

（可能需要在wsl2中运行）

进入后端目录：

```bash
cd backend
```

建议创建虚拟环境：

```bash
python -m venv .venv
```

激活虚拟环境。

Windows Git Bash：

```bash
source .venv/Scripts/activate
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
```

安装依赖：

```bash
pip install -r requirements.txt
```

复制环境变量文件：

```bash
cp .env.example .env
```

编辑 `.env`，填写 API Key 和模型路径。

启动后端：

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 6006
```

后端默认监听：

```text
http://localhost:6006
```

健康检查：

```text
http://localhost:6006/api/health
```

### 1.2 启动主前端 `frontend-vue2/`

新开一个终端，进入主前端目录：

```bash
cd frontend-vue2
```

安装依赖：

```bash
npm install
```

启动开发服务：

```bash
npm run serve
```

Webpack 开发服务默认端口在 `webpack.config.js` 中配置为：

```text
6008
```

访问：

```text
http://localhost:6008
```

前端开发服务会把 `/api` 请求代理到：

```text
http://localhost:6006
```

注意后端服务需要先启动。

---

## 2. 项目架构

```text
MODAT/
├── backend/                 # FastAPI 后端服务
│   ├── app/
│   │   ├── main.py          # 后端入口，定义 API、上传、审核、问答、知识库接口
│   │   ├── core/            # 配置、向量库、Embedding 等核心能力
│   │   ├── graph/           # LangGraph 工作流：问答、审核、向量库操作
│   │   ├── api/             # WebSocket 等 API 辅助模块
│   │   ├── session/         # 会话上下文管理
│   │   └── task/            # 异步任务队列和任务模型
│   ├── knowledge_files/     # 知识库文件目录
│   ├── upload_files/        # 方案审核上传文件目录
│   ├── requirements.txt     # Python 依赖
│   └── .env.example         # 后端环境变量示例
│
├── frontend-vue2/           # Vue 2 主前端
│   ├── src/
│   │   ├── views/           # 页面：First、Home、HomeSingle、KnowledgeFiles 等
│   │   ├── components/      # 聊天、审核面板、知识库、历史记录等组件
│   │   ├── store/           # Vuex 状态管理
│   │   ├── router/          # vue-router 路由配置
│   │   ├── api/             # 前端 API 客户端
│   │   ├── mock/            # Mock 数据与模拟流程
│   │   └── assets/          # 图片、图标等静态资源
│   ├── package.json
│   └── webpack.config.js
│
├── frontend/                # Next.js / React 前端版本
│   ├── src/
│   └── package.json
│
└── MOTA案例.docx            # 示例材料
```

---

## 3. 技术栈

### 后端

- Python
- FastAPI
- Uvicorn
- LangGraph
- LangChain OpenAI / DeepSeek 兼容接口
- ChromaDB
- PyMuPDF
- python-docx
- DuckDuckGo Search
- WebSocket
- vLLM / sentence-transformers

### 主前端：`frontend-vue2/`

- Vue 2.7
- Vuex 3
- vue-router 3
- Element UI
- Axios
- Webpack 5
- marked + DOMPurify

### 备用前端：`frontend/`

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS
- shadcn / Radix UI

---

## 4. 核心功能

### 4.1 智能问答

前端通过聊天界面提交问题，后端进入 QA 工作流。

主要接口：

```text
POST /api/chat
POST /api/chat/stream
```

QA 工作流主要包含：

1. 用户问题接收；
2. 会话上下文读取；
3. 问题脱敏；
4. 意图识别；
5. Query 构造；
6. 知识库检索；
7. 网络检索或多源检索；
8. 冲突识别；
9. 答案生成。

相关文件：

```text
backend/app/main.py
backend/app/graph/qa_workflow.py
backend/app/graph/qa_state.py
backend/app/graph/qa_nodes.py
frontend-vue2/src/components/ChatInterface.vue
frontend-vue2/src/store/modules/chat.js
frontend-vue2/src/api/index.js
```

---

### 4.2 方案审核

用户上传方案文件后，前端会切换到文档审核模式，并在发送审核要求时调用后端审核接口。

主要接口：

```text
POST /api/upload
POST /api/review
```

当前支持上传：

```text
.pdf
.doc
.docx
.txt
```

当前前端实现逻辑：

1. 首页点击“方案审核”进入 `/content`；
2. `/content` 对应 `Home.vue`；
3. 用户在 `ChatInterface.vue` 上传文件；
4. 上传成功后前端提交：

```js
SET_TASK_MODE('document-review')
SET_REVIEW_PHASE('document')
```

5. 左侧显示 `DocumentReviewPanel.vue`；
6. 用户发送审核要求；
7. 前端调用 `/api/review`；
8. 后端执行 Review LangGraph 工作流；
9. 返回审核结果和步骤信息。

相关文件：

```text
backend/app/main.py
backend/app/graph/review_workflow.py
backend/app/graph/review_state.py
backend/app/graph/review_nodes.py
frontend-vue2/src/components/ChatInterface.vue
frontend-vue2/src/components/DocumentReviewPanel.vue
frontend-vue2/src/store/modules/chat.js
frontend-vue2/src/api/index.js
```

---

### 4.3 知识库管理与向量检索

系统支持上传知识库文件、扫描知识库目录、批量导入向量库、检索和维护向量库数据。

主要接口：

```text
POST /api/knowledge_upload
POST /api/knowledge/batch_import
GET  /api/knowledge/scan
GET  /api/knowledge/tree
GET  /api/knowledge/download
GET  /api/knowledge/preview

POST /api/vectordb/add
POST /api/vectordb/qa
POST /api/vectordb/search
POST /api/vectordb/update
POST /api/vectordb/delete
GET  /api/vectordb/list
```

相关文件：

```text
backend/app/main.py
backend/app/core/vector_store.py
backend/app/graph/vectordb_workflow.py
frontend-vue2/src/components/KnowledgeManager.vue
frontend-vue2/src/components/FilePreview.vue
frontend-vue2/src/api/index.js
```

---

## 5. 前端页面逻辑

主前端首页位于：

```text
frontend-vue2/src/views/First.vue
```

首页有两个入口：

```vue
<div class="btn" @click="navigateTo('/content')">方案审核</div>
<div class="btn" @click="navigateTo('/single')">智能问询</div>
```

路由配置位于：

```text
frontend-vue2/src/router/index.js
```

当前路由关系：

| 入口 | 路由 | 页面组件 |
| --- | --- | --- |
| 方案审核 | `/content` | `Home.vue` |
| 智能问询 | `/single` | `HomeSingle.vue` |
| 知识库 | `/knowledge` | `KnowledgeFiles.vue` |

需要注意：`Home.vue` 和 `HomeSingle.vue` 当前结构非常接近，且 Vuex 默认状态是：

```js
sidebarActive: 'chat'
taskMode: 'qa'
reviewPhase: 'document'
layoutMode: 'double'
```

因此从“方案审核”和“智能问询”进入后，初始视觉上都可能像是同一个聊天界面。当前方案审核模式主要由“上传文件”动作触发，而不是由路由入口直接触发。

---

## 6. 常用 API 概览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/` | API 基本信息 |
| GET | `/api/health` | 健康检查 |
| POST | `/api/chat` | 普通问答 |
| POST | `/api/chat/stream` | 流式问答 |
| POST | `/api/review` | 方案审核 |
| POST | `/api/upload` | 上传待审核方案文件 |
| POST | `/api/knowledge_upload` | 上传知识库文件 |
| POST | `/api/knowledge/batch_import` | 批量导入知识库到向量库 |
| GET | `/api/knowledge/scan` | 扫描知识库文件 |
| GET | `/api/knowledge/tree` | 获取知识库目录树 |
| GET | `/api/knowledge/download` | 下载知识库文件 |
| GET | `/api/knowledge/preview` | 预览知识库文件 |
| POST | `/api/vectordb/add` | 添加向量库文档 |
| POST | `/api/vectordb/qa` | 向量库问答 |
| POST | `/api/vectordb/search` | 向量库检索 |
| POST | `/api/vectordb/update` | 更新向量库数据 |
| POST | `/api/vectordb/delete` | 删除向量库数据 |
| GET | `/api/vectordb/list` | 查看向量库数据 |
| WS | `/ws/{session_id}` | WebSocket 会话 |
