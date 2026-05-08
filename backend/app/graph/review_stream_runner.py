"""方案审核流式 runner。

该模块复用现有 review_nodes 与 review_workflow.route_history，
只改变过程事件输出方式，不改变审核业务判断。
"""

import asyncio
import contextlib
import logging
import sys
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple

from .review_state import ReviewState
from .review_workflow import route_history
from .review_nodes import (
    node_desensitize,
    node_check_history,
    node_parse_document,
    node_struct_extract,
    node_build_queries,
    node_multi_source_search,
    node_conflict_resolve,
    node_inquiry_check,
    node_generate_review,
)
from .review_events import (
    NODE_DONE_MESSAGES,
    NODE_TO_STEP_ID,
    build_command_log_event,
    build_document_patch_event,
    build_node_log_event,
    build_node_start_event,
    build_step_patch_event,
    build_workflow_init_event,
)

Emit = Callable[[Dict[str, Any]], Awaitable[None]]
NodeFunc = Callable[[ReviewState], Dict[str, Any]]
NodeSpec = Tuple[str, Optional[str], NodeFunc]


class _RealtimeReviewNodeLogHandler(logging.Handler):
    """把 review_workflow 日志实时投递到 SSE 事件队列。"""

    def __init__(self, loop: asyncio.AbstractEventLoop, emit: Emit, step_id: str) -> None:
        super().__init__(level=logging.INFO)
        self.loop = loop
        self.emit_callback = emit
        self.step_id = step_id
        self.setFormatter(logging.Formatter("%(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
            future = asyncio.run_coroutine_threadsafe(
                self.emit_callback(build_node_log_event(self.step_id, message)),
                self.loop,
            )
            future.add_done_callback(lambda item: item.exception())
        except Exception:
            self.handleError(record)


class _RealtimeCommandLogHandler(logging.Handler):
    """把后端命令行 logger 输出同步到审核 SSE。"""

    def __init__(self, loop: asyncio.AbstractEventLoop, emit: Emit) -> None:
        super().__init__(level=logging.INFO)
        self.loop = loop
        self.emit_callback = emit
        self.setFormatter(logging.Formatter("%(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
            future = asyncio.run_coroutine_threadsafe(
                self.emit_callback(
                    build_command_log_event(
                        message=message,
                        level=record.levelname,
                        logger=record.name,
                        timestamp=datetime.fromtimestamp(record.created).strftime("%H:%M:%S"),
                    )
                ),
                self.loop,
            )
            future.add_done_callback(lambda item: item.exception())
        except Exception:
            self.handleError(record)


class _StreamToCommandLog:
    """把 print/stdout/stderr 行输出桥接成 command_log 事件。"""

    def __init__(self, loop: asyncio.AbstractEventLoop, emit: Emit, stream, level: str, logger_name: str) -> None:
        self.loop = loop
        self.emit_callback = emit
        self.stream = stream
        self.level = level
        self.logger_name = logger_name
        self.buffer = ""

    def write(self, text: str) -> int:
        if not text:
            return 0
        self.stream.write(text)
        self.stream.flush()
        self.buffer += text
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            self._emit_line(line.rstrip("\r"))
        return len(text)

    def flush(self) -> None:
        self.stream.flush()
        if self.buffer.strip():
            self._emit_line(self.buffer.strip())
            self.buffer = ""

    def isatty(self) -> bool:
        return self.stream.isatty() if hasattr(self.stream, "isatty") else False

    def _emit_line(self, line: str) -> None:
        if not line.strip():
            return
        future = asyncio.run_coroutine_threadsafe(
            self.emit_callback(
                build_command_log_event(
                    message=line,
                    level=self.level,
                    logger=self.logger_name,
                    timestamp=datetime.now().strftime("%H:%M:%S"),
                )
            ),
            self.loop,
        )
        future.add_done_callback(lambda item: item.exception())


@contextlib.contextmanager
def capture_command_logs(loop: asyncio.AbstractEventLoop, emit: Emit):
    """在一次审核任务期间捕获 logger 与 print 输出，供前端实时验证。"""
    root_logger = logging.getLogger()
    command_handler = _RealtimeCommandLogHandler(loop, emit)
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = _StreamToCommandLog(loop, emit, old_stdout, "INFO", "stdout")
    sys.stderr = _StreamToCommandLog(loop, emit, old_stderr, "ERROR", "stderr")
    root_logger.addHandler(command_handler)
    try:
        yield
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        root_logger.removeHandler(command_handler)
        command_handler.close()


async def run_review_streaming(
    state: ReviewState,
    emit: Emit,
    build_workflow_steps: Callable[[Dict[str, Any]], list],
    build_review_report: Callable[[Dict[str, Any]], Dict[str, Any]],
    filename: str,
) -> ReviewState:
    """按现有审核语义执行节点，并在执行过程中发送结构化事件。"""
    await emit(build_workflow_init_event())

    prefix_nodes: Tuple[NodeSpec, ...] = (
        ("desensitize", NODE_TO_STEP_ID["desensitize"], node_desensitize),
        ("check_history", NODE_TO_STEP_ID["check_history"], node_check_history),
    )

    loop = asyncio.get_running_loop()
    with capture_command_logs(loop, emit):
        await emit(build_command_log_event(
            message=f"开始审核流式任务 | filename={filename}",
            level="INFO",
            logger="review_stream",
            timestamp=datetime.now().strftime("%H:%M:%S"),
        ))

        for node_name, step_id, node_func in prefix_nodes:
            state = await run_node_with_events(node_name, step_id, node_func, state, emit)

        if route_history(state) == "generate_review":
            await emit({
                "type": "node_log",
                "message": "检测到可复用历史审核结果，本轮跳过完整解析与检索链路",
            })
            pipeline: Tuple[NodeSpec, ...] = (
                ("generate_review", NODE_TO_STEP_ID["generate_review"], node_generate_review),
            )
        else:
            pipeline = (
                ("parse_document", NODE_TO_STEP_ID["parse_document"], node_parse_document),
                ("struct_extract", NODE_TO_STEP_ID["struct_extract"], node_struct_extract),
                ("build_queries", NODE_TO_STEP_ID["build_queries"], node_build_queries),
                ("multi_source_search", NODE_TO_STEP_ID["multi_source_search"], node_multi_source_search),
                ("conflict_resolve", NODE_TO_STEP_ID["conflict_resolve"], node_conflict_resolve),
                ("inquiry_check", NODE_TO_STEP_ID["inquiry_check"], node_inquiry_check),
                ("generate_review", NODE_TO_STEP_ID["generate_review"], node_generate_review),
            )

        for node_name, step_id, node_func in pipeline:
            state = await run_node_with_events(node_name, step_id, node_func, state, emit)
            await emit_node_result(node_name, step_id, state, emit, build_workflow_steps, build_review_report)
        await emit(build_command_log_event(
            message="审核流式任务执行完成，准备生成最终快照",
            level="INFO",
            logger="review_stream",
            timestamp=datetime.now().strftime("%H:%M:%S"),
        ))

    final_report = build_review_report(state)
    await emit({
        "type": "final",
        "status": "done",
        "message": "审核完成，已在左侧生成审核报告和方案优化建议。",
        "fileName": state.get("doc_info", {}).get("filename") or filename,
        "resultSnapshot": final_report,
        "reviewData": {
            "documentContent": state.get("doc_text", ""),
            "documentInfo": state.get("doc_info", {}),
            "fileName": state.get("doc_info", {}).get("filename") or filename,
            "workflow": {"steps": build_workflow_steps(state)},
            "finalReport": final_report,
            "rawSteps": state.get("steps", []),
        },
        "rawSteps": state.get("steps", []),
    })
    return state


async def run_node_with_events(
    node_name: str,
    step_id: Optional[str],
    node_func: NodeFunc,
    state: ReviewState,
    emit: Emit,
) -> ReviewState:
    """执行单个同步节点，并发送开始/完成/失败事件。"""
    if step_id:
        start_event = build_node_start_event(node_name, step_id)
        if start_event:
            await emit(start_event)
        await emit(build_step_patch_event(step_id, {"status": "in_progress"}))

    review_logger = logging.getLogger("review_workflow")
    log_handler = None
    if step_id:
        log_handler = _RealtimeReviewNodeLogHandler(asyncio.get_running_loop(), emit, step_id)
        review_logger.addHandler(log_handler)
    try:
        next_state = await asyncio.to_thread(node_func, state)
    except Exception as exc:
        if step_id:
            await emit(build_step_patch_event(step_id, {"status": "error"}))
            await emit(build_node_log_event(step_id, f"执行失败：{exc}"))
        raise
    finally:
        if log_handler:
            review_logger.removeHandler(log_handler)
            log_handler.close()

    if step_id:
        await emit(build_node_log_event(step_id, NODE_DONE_MESSAGES.get(node_name, "节点执行完成")))
        await emit(build_step_patch_event(step_id, {"status": "done"}))
    return next_state


async def emit_node_result(
    node_name: str,
    step_id: Optional[str],
    state: ReviewState,
    emit: Emit,
    build_workflow_steps: Callable[[Dict[str, Any]], list],
    build_review_report: Callable[[Dict[str, Any]], Dict[str, Any]],
) -> None:
    """节点结束后从 state 中抽取当前可展示的局部结果。"""
    steps = build_workflow_steps(state)
    step_by_id = {step.get("id"): step for step in steps}

    if node_name == "parse_document":
        await emit(build_document_patch_event(state.get("doc_text", ""), state.get("doc_info", {})))
        doc_step = step_by_id.get("doc-analysis")
        if doc_step:
            await emit(build_step_patch_event("doc-analysis", {"details": doc_step.get("details", {})}))
        return

    if step_id and step_id in step_by_id:
        patch: Dict[str, Any] = {"details": step_by_id[step_id].get("details", {})}
        if "progress" in step_by_id[step_id]:
            patch["progress"] = step_by_id[step_id].get("progress")
        await emit(build_step_patch_event(step_id, patch))

    if node_name == "generate_review":
        rewrite_step = step_by_id.get("plan-rewrite")
        if rewrite_step:
            await emit(build_step_patch_event("plan-rewrite", {
                "status": "done",
                "details": rewrite_step.get("details", {}),
            }))
        report = build_review_report(state)
        await emit({
            "type": "report_chunk",
            "section": "summary",
            "content": report.get("summary", ""),
        })
        await emit({
            "type": "result_snapshot",
            "resultSnapshot": report,
        })
